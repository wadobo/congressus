import numpy as np
import random

from autoslug import AutoSlugField
from django import forms
from django.urls import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from invs.utils import get_sold_invs
from .widgets import HTMLWidget


TICKET_DATE_FORMATS = (
    ('start', _('Date and start time')),
    ('complete', _('Date, start and end time')),
    ('onlydate', _('Only date')),
)

INV_TYPES = (
    ('invited', _('Invited')),
    ('speaker', _('Speaker')),
    ('student', _('Student')),
)

FIELD_TYPES = (
    ('email', _('Email')),
    ('tel', _('Phone')),
    ('url', _('URL')),
    ('text', _('Text')),
    ('textarea', _('TextArea')),
    ('check', _('CheckBox')),
    ('select', _('Select')),
    ('html', _('HTML')),
)

DIRECTIONS = (
    ('u', _('Up')),
    ('l', _('Left')),
    ('r', _('Right')),
    ('d', _('Down')),
)


class Discount(models.Model):
    DISCOUNT_TYPES = (
        ('percent', _('Percent')),
        ('amount', _('Amount')),
    )

    name = models.CharField(_('name'), max_length=200, unique=True)
    type = models.CharField(_('type'), max_length=8, choices=DISCOUNT_TYPES, default='percent')
    value = models.IntegerField(_('value'), default=0)
    unit = models.BooleanField(_('per unit'), default=True)

    def apply_to(self, t):
        if not self.value:
            return t
        res = t
        if self.type == 'percent':
            res -= res*(self.value/100.0)
        elif self.type == 'amount':
            res -= self.value
        return res

    def __str__(self):
        return '%s: %s %s' % (self.name, self.value, '%' if self.type == 'percent' else '')


class Event(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    slug = AutoSlugField(populate_from='name')

    info = models.TextField(_('info'), blank=True, null=True)
    active = models.BooleanField(_('active'), default=False)
    admin = models.EmailField(_('admin email'), blank=True, null=True)
    discounts = models.ManyToManyField(Discount, related_name='events',
                                      blank=True,
                                      verbose_name=_('discounts'))

    # fields to activate/deactivate tickets sale
    ticket_sale_enabled = models.BooleanField(_('sale enabled'), default=True)
    ticket_sale_message = models.TextField(_('sale message'),
       help_text=_('Message to show when the ticket sale is disabled'),
       blank=True, null=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('multipurchase', kwargs={'ev': self.slug})

    def get_email(self):
        try:
            return self.email
        except:
            return None

    def get_sessions(self):
        return Session.objects.filter(space__event=self)

    def sold(self):
        return sum(i.sold() for i in self.get_sessions())


class SeatMap(models.Model):
    name = models.CharField(_('name'), max_length=300)
    img = models.ImageField(_('map image'), upload_to='maps',
                            blank=True, null=True)

    scene_top = models.IntegerField(_('scene top limit'), default=0)
    scene_bottom = models.IntegerField(_('scene bottom limit'), default=0)
    scene_left = models.IntegerField(_('scene left limit'), default=0)
    scene_right = models.IntegerField(_('scene right limit'), default=0)

    class Meta:
        verbose_name = _('seat Map')
        verbose_name_plural = _('seat Maps')

    def __str__(self):
        return self.name

    def get_table(self):
        layouts = list(self.layouts.all())
        indexes = {(i.top, i.left): i  for i in layouts}
        max_vertical = max([i.top for i in layouts], default=0)
        max_horizontal = max([i.left for i in layouts], default=0)

        for r in range(self.scene_top, self.scene_bottom + 1):
            for c in range(self.scene_left, self.scene_right + 1):
                indexes[(r, c)] = 'scene'

        table = []
        for r in range(0, max_vertical + 1):
            row = []
            for c in range(0, max_horizontal + 1):
                index = (r, c)
                row.append(indexes.get(index, ''))
            table.append(row)
        return table


class Gate(models.Model):
    event = models.ForeignKey(Event, related_name='gates', verbose_name=_('event'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        verbose_name = _('gate')
        verbose_name_plural = _('gates')

    def __str__(self):
        return self.name


class SeatLayout(models.Model):
    map = models.ForeignKey(SeatMap, related_name='layouts', verbose_name=_('map'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=300)
    top = models.IntegerField(_('top'), default=0)
    left = models.IntegerField(_('left'), default=0)
    direction = models.CharField(_('direction'), max_length=2, choices=DIRECTIONS, default='d')
    layout = models.TextField(_('seats layout'),
                              help_text=_('the layout to select the '
                                          'numbered seat. '
                                          'L = Free, _ = Space, R = Reserved'))

    column_start_number = models.IntegerField(_('column start number'), default=1)
    gate = models.ForeignKey(Gate, blank=True, null=True, verbose_name=_('gate'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('seat Layout')
        verbose_name_plural = _('seat Layouts')

    def __str__(self):
        return self.name

    def glyph(self):
        g = {
            'u': 'glyphicon-arrow-up',
            'l': 'glyphicon-arrow-left',
            'r': 'glyphicon-arrow-right',
            'd': 'glyphicon-arrow-down',
        }

        return g[self.direction]

    def rows(self):
        return np.array([list(row) for row in self.layout.split()])

    def real_rows(self):
        """ Show rows in real position. """
        if self.direction == 'd':
            return np.flipud(self.rows())
        elif self.direction == 'u':
            return self.rows()
        elif self.direction == 'l':
            return np.transpose(self.rows())
        elif self.direction == 'r':
            return np.fliplr(np.rot90(self.rows()))

    def cols(self):
        return np.transpose(self.rows())

    def real_cols(self):
        """ Show cols in real position. """
        return np.transpose(self.real_rows())

    def free(self):
        return self.layout.count('L')

    def free_seats(self, session):
        from tickets.models import TicketSeatHold
        n = TicketSeatHold.objects.filter(session=session, layout=self).count()
        return self.free() - n

    def contiguous_seats(self, amount, holded, col_start, row_rand=0):
        """ Free contiguous seats in a row. """

        layout = self.real_rows()
        for h in holded: # Changed free by holded seats before search
            r, c = h.seat.split("-")
            layout[int(r) - 1, int(c) - self.column_start_number] = h.type
        nrow = 1
        avail = {}
        for row in layout:
            free = ''.join(row).find(amount*'L')
            if free != -1:
                avail = {'row': nrow, 'col_ini': free + 1, 'col_end': free + amount + 1}
                if row_rand > 0:
                    row_rand -= 1
                else:
                    break
            nrow += 1
        return avail


class Space(models.Model):
    event = models.ForeignKey(Event, related_name='spaces', verbose_name=_('event'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=300)
    slug = AutoSlugField(populate_from='name')

    capacity = models.IntegerField(_('capacity'), default=100)
    numbered = models.BooleanField(_('numbered'), default=False)
    seat_map = models.ForeignKey(SeatMap, related_name='spaces', null=True, blank=True, verbose_name=_('seat map'), on_delete=models.CASCADE)

    order = models.IntegerField(_('order'), default=0)

    def get_next_sessions(self):
        now = timezone.now()
        return self.sessions.filter(end__gte=now, active=True)

    class Meta:
        ordering = ['order']
        verbose_name = _('space')
        verbose_name_plural = _('spaces')

    def __str__(self):
        return '%s - %s' % (self.event, self.name)


class Session(models.Model):
    space = models.ForeignKey(Space, related_name='sessions', verbose_name=_('space'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=300)
    slug = AutoSlugField(populate_from='name')

    short_name = models.CharField(_('short name'), max_length=3, blank=True, null=True)

    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'))

    price = models.FloatField(_('ticket price'), default=10)
    window_price = models.FloatField(_('price in the ticket window'), default=10)
    tax = models.IntegerField(_('ticket tax percentage'), default=21)

    template = models.ForeignKey("TicketTemplate", verbose_name=_('template'), on_delete=models.CASCADE)
    autoseat_mode = models.CharField(_('autoseat mode'), max_length=300, default='ASC',
            help_text="ASC, DESC, RANDOM or LIST: layout_name1,layout_name2")

    dateformat = models.CharField(_('date format'), max_length=50, default='start', choices=TICKET_DATE_FORMATS)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start']
        verbose_name = _('session')
        verbose_name_plural = _('sessions')

    def __str__(self):
        return '%s - %s' % (self.space, self.name)

    def short(self):
        return '%s - %s' % (self.space.name, self.name)

    def price_without_tax(self):
        return self.price / (1 + self.tax / 100.0)

    def window_price_without_tax(self):
        return self.window_price / (1 + self.tax / 100.0)

    def event(self):
        return self.space.event

    def sold(self):
        sold = self.tickets.filter(confirmed=True).count()
        return sold

    def have_places(self, number=1):
        s_t = self.sold()
        s_i = get_sold_invs(self)
        return (s_t + s_i + number) < self.space.capacity

    def is_seat_available(self, layout, row, column, client=None):
        holded = self.is_seat_holded(layout, row, column, client)
        return not holded

    def is_seat_holded(self, layout, row, column, client=None):
        seat = row + '-' + column
        holds = self.seat_holds.filter(layout=layout, seat=seat)
        if client:
            holds = holds.exclude(client=client, type='H')
        if holds.exists():
            return holds[0].type
        else:
            return ''

    def seats_holded(self, layout=None, type=None, client=None):
        query = Q()
        if type:
            query &= Q(type=type)
        if layout:
            query &= Q(layout=layout)
        holds = self.seat_holds.filter(query)
        if client:
            holds = holds.exclude(client=client)
        return holds

    def places(self):
        self.space.capacity


class ExtraSession(models.Model):
    orig = models.ForeignKey(Session, related_name='orig_sessions', verbose_name=_('orig'), on_delete=models.CASCADE)
    extra = models.ForeignKey(Session, related_name='extra_sessions', verbose_name=_('extra'), on_delete=models.CASCADE)
    start = models.DateTimeField(_('Start at'))
    end = models.DateTimeField(_('End at'))
    used = models.BooleanField(_('used'), default=False)

    class Meta:
        verbose_name = _('extra session')
        verbose_name_plural = _('extra sessions')

    def __str__(self):
        return '%s -> %s' % (self.orig, self.extra)


class ConfirmEmail(models.Model):
    event = models.OneToOneField(Event, related_name='email', verbose_name=_('event'), on_delete=models.CASCADE)
    subject = models.CharField(_('subject'), max_length=300)
    body = models.TextField(_('body'))

    class Meta:
        verbose_name = _('confirm email')
        verbose_name_plural = _('confirm emails')

    def get_absolute_url(self):
        return reverse('email_confirm_preview', kwargs={'id': self.id})


    def __str__(self):
        return "ConfirmEmail - %s" % self.event


class EmailAttachment(models.Model):
    email = models.ForeignKey(ConfirmEmail, related_name='attachs', verbose_name=_('email'), on_delete=models.CASCADE)
    attach = models.FileField(_('attach'), upload_to='attachments')

    class Meta:
        verbose_name = _('email attachment')
        verbose_name_plural = _('email attachments')


class InvCode(models.Model):
    event = models.ForeignKey(Event, related_name='codes', verbose_name=_('event'), on_delete=models.CASCADE)
    code = models.CharField(_('code'), max_length=10, blank=True, null=True)
    person = models.CharField(_('for person'), max_length=100, blank=True, null=True)
    used = models.BooleanField(_('used'), default=False)
    type = models.CharField(_('type'), choices=INV_TYPES, default='invited', max_length=15)

    class Meta:
        verbose_name = _('invitation code')
        verbose_name_plural = _('invitation codes')

    def __str__(self):
        return "%s - %s" % (self.code, self.type)


class TicketField(models.Model):
    event = models.ForeignKey(Event, related_name='fields', verbose_name=_('event'), on_delete=models.CASCADE)
    order = models.IntegerField(_('order'), default=0)
    type = models.CharField(_('type'), max_length=100, choices=FIELD_TYPES, default='text')
    label = models.TextField(_('label'))
    help_text = models.CharField(_('help text'), max_length=1000, blank=True, null=True)
    required = models.BooleanField(_('required'), default=False)
    options = models.CharField(_('options'), max_length=500,
                               help_text='comma separated values, only for select type',
                               blank=True, null=True)
    show_in_tws = models.BooleanField(_('show in ticket window sale'), default=False,
            help_text='Only can show one field per event. If you check this field, other field could be unchecked')

    class Meta:
        ordering = ['order']
        verbose_name = _('ticket field')
        verbose_name_plural = _('ticket fields')

    def form_type(self):
        opts = self.options or ''
        choices = ((i, i) for i in map(str.strip, opts.split(',')))

        types = {
            'html': forms.CharField(widget=HTMLWidget),
            'text': forms.CharField(),
            'textarea': forms.CharField(widget=forms.Textarea),
            'check': forms.BooleanField(),
            'select': forms.ChoiceField(choices=choices),
            'email': forms.EmailField(),
            'url': forms.URLField(),
            'tel': forms.CharField(
                    validators=[ RegexValidator(r'^\+?[0-9]+$', _('Enter a valid phone')) ],
            ),
        }

        field = types[self.type]

        field.label = mark_safe(self.label)
        field.help_text = self.help_text
        if not self.required:
            field.required = False

        return field


@receiver(post_save, sender=TicketField)
def unchecked(sender, instance, created, raw, using, update_fields, **kwargs):
    if instance.show_in_tws:
        for tf in TicketField.objects.filter(event=instance.event, show_in_tws=True).exclude(pk=instance.pk):
            tf.show_in_tws = False
            tf.save()


@receiver(post_save, sender=InvCode)
def gencode(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.code:
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        instance.code = ''.join(random.choice(chars) for _ in range(10))
        instance.save()


class TicketTemplate(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    header = models.ImageField(_('header'), upload_to='templheader', blank=True, null=True)
    sponsors = models.ImageField(_('sponsors'), upload_to='templsponsors', blank=True, null=True)
    note = models.CharField(_('previous note'), max_length=200, blank=True, null=True)
    links = models.CharField(_('links'), max_length=200, blank=True, null=True)
    info = models.TextField(
        _('next note'),
        help_text=_(
            'change fontsize: &ltfont size=6&gtNOTE&lt/font&gt</br>'
            'bold: &ltb&gtNOTE&lt/b&gt'
        ),
        blank=True,
        null=True
    )
    contributors = models.ImageField(_('footer'), upload_to='templcontributors', blank=True, null=True)

    pagesize_width = models.FloatField(_('pagesize width'), help_text=_('in cm'), default=15.92)
    pagesize_height = models.FloatField(_('pagesize height'), help_text=_('in cm'), default=24.62)
    left_margin = models.FloatField(_('left margin'), help_text=_('in cm'), default=2.54)
    right_margin = models.FloatField(_('right margin'), help_text=_('in cm'), default=2.54)
    bottom_margin = models.FloatField(_('bottom margin'), help_text=_('in cm'), default=2.54)
    top_margin = models.FloatField(_('top margin'), help_text=_('in cm'), default=2.54)
    border_qr = models.FloatField(_('border qr'), default=4)
    qr_size = models.FloatField(_('qr size'), help_text=_('in cm'), default=10)
    extra_style = models.TextField(
        _('extra style'),
        help_text=_('Extra style in css for configure template'),
        blank=True,
        null=True,
    )
    extra_js = models.TextField(
        _('extra js'),
        help_text=_('Extra js for configure template'),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('ticket template')
        verbose_name_plural = _('ticket templates')

    @property
    def footer(self):
        return self.contributors

    @property
    def previous_note(self) -> str:
        return self.note or ''

    @property
    def next_note(self) -> str:
        return self.info or ''

    @property
    def is_vertical(self) -> bool:
        return self.pagesize_width < self.pagesize_height

    @classmethod
    def get_all_templates_dict(cls) -> dict[int, str]:
        return {tpl.id: tpl.name for tpl in cls.objects.all()}

    def get_absolute_url(self):
        return reverse('template_preview', kwargs={'id': self.id})

    def config_in(self, unit: float) -> dict[str, float]:
        return {
            'pagesize': (self.pagesize_width * unit, self.pagesize_height * unit),
            'leftMargin': self.left_margin * unit,
            'rightMargin': self.right_margin * unit,
            'bottomMargin': self.bottom_margin * unit,
            'topMargin': self.top_margin * unit,
        }

    def __str__(self):
        return self.name
