import base64
import string
import random
from io import BytesIO

import qrcode
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import formats, timezone
from django.utils.translation import ugettext_lazy as _

from events.models import Event
from events.models import Session
from events.models import Gate
from events.models import SeatLayout
from events.ticket_pdf import TicketPDF
from tickets.models import BaseExtraData
from tickets.models import TicketSeatHold
from tickets.utils import get_seats_by_str

from django.db.models.signals import post_delete


def short_hour(date_time):
    if timezone.is_aware(date_time):
        date_time = timezone.localtime(date_time)
    return formats.date_format(date_time, 'H:i')


class InvitationType(models.Model):
    name = models.CharField(_('name'), max_length=200)
    is_pass = models.BooleanField(_('is pass'), default=False)
    one_time_for_session = models.BooleanField(
        _('one time for session'),
        default=False,
        help_text=_(
            'This is used for passes that will be '
            'only valid one time for each session. '
            'Invitations always have only one use. '
            'So this is ignored in invitations.'
        )
    )

    event = models.ForeignKey(
        Event,
        related_name='invitation_types',
        verbose_name=_('event'),
        on_delete=models.CASCADE
    )
    sessions = models.ManyToManyField(
        Session,
        related_name='invitation_types',
        blank=True,
        verbose_name=_('sessions')
    )

    gates = models.ManyToManyField(Gate, blank=True, verbose_name=_('gates'))
    start = models.DateTimeField(_('start date'), null=True, blank=True)
    end = models.DateTimeField(_('end date'), null=True, blank=True)
    template = models.ForeignKey("events.TicketTemplate", verbose_name=_('template'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('invitation type')
        verbose_name_plural = _('invitation types')
        ordering = ('-event__name', 'name')

    def __str__(self):
        return self.name


class Invitation(models.Model, BaseExtraData):
    type = models.ForeignKey(InvitationType, related_name='invitations',
                             verbose_name=_('invitation type'), on_delete=models.CASCADE)

    generator = models.ForeignKey('InvitationGenerator', related_name='invitations',
                                  null=True, blank=True, verbose_name=_('generator'), on_delete=models.CASCADE)

    order = models.CharField(_('order'), max_length=200, unique=True)
    created = models.DateTimeField(_('created at'), auto_now_add=True)
    extra_data = models.TextField(_('extra data'), blank=True, null=True)
    is_pass = models.BooleanField(_('is pass'), default=False)

    # row-col
    seat_layout = models.ForeignKey(SeatLayout, null=True, blank=True, verbose_name=_('seat layout'), on_delete=models.CASCADE)
    seat = models.CharField(_('seat'), max_length=20, null=True, blank=True)
    name = models.CharField(_('name'), max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = _('invitation')
        verbose_name_plural = _('invitations')

    @property
    def used(self):
        return self.usedin.exists()

    @property
    def used_date(self):
        try:
            return self.usedin.all()[0].date
        except:
            return None

    @property
    def wcode(self) -> str:
        if self.generator:
            return 'GEN' + str(self.generator.id)

        return 'INV'

    @property
    def initials(self):
        if self.type.is_pass:
            return "PAS"

        return "INV"

    @property
    def text(self):
        if self.generator:
            return self.generator.concept

        return self.type.name

    @property
    def date(self):
        sstart = self.type.start
        send = self.type.end

        if not sstart or not send:
            return ''

        return _('%(date)s (%(start)s)') % {
            'date': formats.date_format(sstart, "l d/m/Y"),
            'start': short_hour(sstart),
        }

    @property
    def seatinfo(self):
        seatinfo = ''
        if self.seat:
            seatdata = {
                'layout': self.seat_layout.name,
                'row': self.seat_row(),
                'col': self.seat_column()
            }
            seatinfo = _('SECTOR: %(layout)s ROW: %(row)s SEAT: %(col)s') % seatdata
            seatinfo = f'<font size=11><b>{seatinfo}</b></font><br/>'
        return seatinfo

    @property
    def total_price(self) -> str:
        if self.sold_in_window:
            price = self.get_window_price()
        else:
            price = self.get_price()

        if not price:
            return ''

        price = _('%4.2f €') % price
        tax = self.get_tax()

        taxtext = _('TAX INC.')
        return f'<font class="price">{price}</font>   <font class="tax">{tax}% {taxtext}</font>'

    def is_used(self, session):
        return self.usedin.filter(session=session).exists()

    def get_used_date(self, session):
        try:
            return self.usedin.get(session=session).date
        except:
            return None

    def set_used(self, session):
        i, created = InvUsedInSession.objects.get_or_create(session=session, inv=self)
        i.save()

    def get_gate_name(self):
        return ', '.join(i.name for i in self.type.gates.all())

    def gen_order(self, starts=''):
        """ Generate order for passes and invitations """
        starts = starts or settings.INVITATION_ORDER_START
        chars = string.ascii_uppercase + string.digits
        l = 8
        if hasattr(settings, 'ORDER_SIZE'):
            l = settings.ORDER_SIZE

        l -= len(starts)

        order = ''
        used = True
        while used:
            order = ''.join(random.choice(chars) for _ in range(l))
            order = starts + order
            used = self.is_order_used(order)
        self.order = order
        self.save()

    @staticmethod
    def gen_orders(starts='', amount=10) -> tuple[str]:
        length = 8
        orders = set()
        chars = string.ascii_uppercase + string.digits
        while len(orders) < amount:
            orders.add(starts + ''.join(random.choice(chars) for _ in range(length)))
        return tuple(orders)

    def is_order_used(self, order):
        return Invitation.objects.filter(order=order).exists()

    def save_extra_sessions(self):
        data = []
        for session in self.type.sessions.all():
            for extra in session.orig_sessions.all():
                prev = self.get_extra_session(extra.extra.id)
                data.append({
                    'session': extra.extra.id,
                    'start': timezone.make_naive(extra.start).strftime(settings.DATETIME_FORMAT),
                    'end': timezone.make_naive(extra.end).strftime(settings.DATETIME_FORMAT),
                    'used': prev['used'] if prev else extra.used
                })
        self.set_extra_data('extra_sessions', data)

    @property
    def sold_in_window(self):
        return False

    def get_price(self):
        if self.generator:
            return self.generator.price

        return 0

    def get_tax(self):
        if self.generator:
            return self.generator.tax
        return 0

    def gen_pdf(self):
        return TicketPDF(self).generate()

    def gen_thermal(self):
        return TicketPDF(self).generate()

    def cseat(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return _('L%(layout)s-R%(row)s-C%(col)s') % {'layout': self.seat_layout.name, 'row': row, 'col': column}
    cseat.short_description = _('seat')

    def seat_row(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return row

    def seat_column(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return column

    def remove_hold_seats(self):
        if self.seat_layout and self.seat:
            for s in self.type.sessions.all():
                tsh = TicketSeatHold.objects.filter(
                        session=s,
                        layout=self.seat_layout,
                        type='R',
                        seat=self.seat)
                if tsh:
                    tsh.delete()

    def gen_qr(self, qr_size: float = 10, border: int = 4):
        """
        border: default is 4, which is the minimum according to the specs
        """
        stream = BytesIO()
        img = qrcode.make(
            self.order,
            box_size=qr_size + 2 * border,
            border=border,
        )
        img.save(stream, format="png")
        return base64.b64encode(stream.getvalue()).decode("utf8")

    def __str__(self):
        return self.order


class InvUsedInSession(models.Model):
    inv = models.ForeignKey(Invitation, related_name='usedin', verbose_name=_('invitation'), on_delete=models.CASCADE)
    session = models.ForeignKey(Session, related_name='usedby', verbose_name=_('session'), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('invitation used in')
        verbose_name_plural = _('invitations used in')


class InvitationGenerator(models.Model):
    type = models.ForeignKey(InvitationType, verbose_name=_('type'), on_delete=models.CASCADE)
    amount = models.IntegerField(_('amount'), default=1)
    price = models.IntegerField(_('price'), blank=True, null=True)
    tax = models.IntegerField(_('tax'), null=True)
    concept = models.CharField(_('concept'), max_length=200)
    seats = models.CharField(_('seats'), max_length=1024, blank=True, null=True,
            help_text="C1[1-1,1-3]; C2[2-1:2-4]")
    created = models.DateTimeField(_('created at'), auto_now_add=True)

    def __str__(self):
        return '{} -{} - {}'.format(self.type, self.amount, self.concept)

    class Meta:
        verbose_name = _('invitation generator')
        verbose_name_plural = _('invitation generators')
        ordering = ('-created',)


    def window_code(self):
        '''
        This is a generator code, but use the name window_code to be the same
        of tickets. Example code: INVMMDDHHMM
        '''
        prefix = 'INV'
        postfix = self.created.strftime('%m%d%H%M')
        return prefix + postfix

    def get_seats(self):
        return get_seats_by_str(self.type.sessions.all(), self.seats)

    def clean(self):
        super().clean()
        # only validate on creation
        if self.seats and not self.id:
            seats = 0
            for val in self.get_seats().values():
                seats += len(val)
            if seats != self.amount:
                raise ValidationError(_("Seats number should be equal to amount"))

    def save(self, *args, **kwargs):
        should_generate = not self.id
        super().save(*args, **kwargs)
        if should_generate:
            self.generate()

    def generate(self):
        # SEAT LAYOUTS
        seat_list = []
        if self.seats:
            seats = self.get_seats()
            layouts = SeatLayout.objects.filter(name__in=seats.keys())
            for layout in layouts:
                seat_list += [[layout, value] for value in seats.get(layout.name)]

        # ORDERS
        orders = Invitation.gen_orders(amount=self.amount)
        invalid_orders = Invitation.objects.filter(order__in=orders).values_list('order', flat=True)

        ## Extra sessions
        data = []
        session_first = self.type.sessions.first()
        for session in self.type.sessions.all():
            for extra in session.orig_sessions.all():
                data.append({
                    'session': extra.extra.id,
                    'start': timezone.make_naive(extra.start).strftime(settings.DATETIME_FORMAT),
                    'end': timezone.make_naive(extra.end).strftime(settings.DATETIME_FORMAT),
                    'used': extra.used
                })

        invis = []
        for n in range(self.amount):
            invi = Invitation(type=self.type, generator=self, is_pass=self.type.is_pass)
            if seat_list:
                invi.seat_layout, invi.seat = seat_list[n]

            invi.order = orders[n]
            if invi.order in invalid_orders:
                invi.gen_order()

            invi.set_extra_data('extra_sessions', data)
            invis.append(invi)

            if seat_list:
                tsh, new = TicketSeatHold.objects.get_or_create(
                    session=session_first,
                    layout=invi.seat_layout,
                    seat=invi.seat,
                    defaults={'type': 'R', 'client': 'INV'},
                )
                if not new:
                    tsh.type = 'R'
                    tsh.client = 'INV'
                    tsh.save()

        Invitation.objects.bulk_create(invis)

def remove_seatholds(sender, instance, using, **kwargs):
    instance.remove_hold_seats()


post_delete.connect(remove_seatholds, Invitation)
