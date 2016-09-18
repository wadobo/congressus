import datetime
import numpy as np

from autoslug import AutoSlugField
from django import forms
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from invs.utils import get_sold_invs


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
)

DIRECTIONS = (
    ('u', _('Up')),
    ('l', _('Left')),
    ('r', _('Right')),
    ('d', _('Down')),
)

DISCOUNT_TYPES = (
    ('percent', _('Percent')),
    ('amount', _('Amount')),
)


class Discount(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    type = models.CharField(_('type'), max_length=8, choices=DISCOUNT_TYPES, default='percent')
    value = models.IntegerField(_('value'), default=0)

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
        sessions = []
        for space in self.spaces.all():
            sessions += list(space.sessions.all())
        return sessions

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
        max_vertical = max(i.top for i in layouts)
        max_horizontal = max(i.left for i in layouts)

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
    event = models.ForeignKey(Event, related_name='gates', verbose_name=_('event'))
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        verbose_name = _('gate')
        verbose_name_plural = _('gates')

    def __str__(self):
        return self.name


class SeatLayout(models.Model):
    map = models.ForeignKey(SeatMap, related_name='layouts', verbose_name=_('map'))
    name = models.CharField(_('name'), max_length=300)
    top = models.IntegerField(_('top'), default=0)
    left = models.IntegerField(_('left'), default=0)
    direction = models.CharField(_('direction'), max_length=2, choices=DIRECTIONS, default='d')
    layout = models.TextField(_('seats layout'),
                              help_text=_('the layout to select the '
                                          'numbered seat. '
                                          'L = Free, _ = Space, R = Reserved'))

    column_start_number = models.IntegerField(_('column start number'), default=1)
    gate = models.ForeignKey(Gate, blank=True, null=True, verbose_name=_('gate'))

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

    def contiguous_seats(self, amount, holded, col_start):
        """ Free contiguous seats in a row. """

        layout = self.real_rows()
        for h in holded: # Changed free by holded seats before search
            r, c = h.seat.split("-")
            layout[int(r) - 1, int(c) - self.column_start_number] = h.type
        nrow = 1
        for row in layout:
            free = ''.join(row).find(amount*'L')
            if free != -1:
                return {'row': nrow, 'col_ini': free + 1, 'col_end': free + amount + 1}
            nrow += 1
        return {}


class Space(models.Model):
    event = models.ForeignKey(Event, related_name='spaces', verbose_name=_('event'))
    name = models.CharField(_('name'), max_length=300)
    slug = AutoSlugField(populate_from='name')

    capacity = models.IntegerField(_('capacity'), default=100)
    numbered = models.BooleanField(_('numbered'), default=False)
    seat_map = models.ForeignKey(SeatMap, related_name='spaces', null=True, blank=True, verbose_name=_('seat map'))

    order = models.IntegerField(_('order'), default=0)

    class Meta:
        ordering = ['order']
        verbose_name = _('space')
        verbose_name_plural = _('spaces')

    def __str__(self):
        return '%s - %s' % (self.event, self.name)


class Session(models.Model):
    space = models.ForeignKey(Space, related_name='sessions', verbose_name=_('space'))
    name = models.CharField(_('name'), max_length=300)
    slug = AutoSlugField(populate_from='name')

    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'))

    price = models.FloatField(_('ticket price'), default=10)
    window_price = models.FloatField(_('price in the ticket window'), default=10)
    tax = models.IntegerField(_('ticket tax percentage'), default=21)

    template = models.ForeignKey("TicketTemplate", blank=True, null=True, verbose_name=_('template'))
    autoseat_mode = models.CharField(_('autoseat mode'), max_length=300, default='ASC',
            help_text="ASC, DESC, RANDOM or LIST: layout_name1,layout_name2")

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
            holds = holds.exclude(client=client)
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
    orig = models.ForeignKey(Session, related_name='orig_sessions', verbose_name=_('orig'))
    extra = models.ForeignKey(Session, related_name='extra_sessions', verbose_name=_('extra'))
    start = models.DateTimeField(_('Start at'))
    end = models.DateTimeField(_('End at'))
    used = models.BooleanField(_('used'), default=False)

    class Meta:
        verbose_name = _('extra session')
        verbose_name_plural = _('extra sessions')

    def __str__(self):
        return '%s -> %s' % (self.orig, self.extra)


class ConfirmEmail(models.Model):
    event = models.OneToOneField(Event, related_name='email', verbose_name=_('event'))
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
    email = models.ForeignKey(ConfirmEmail, related_name='attachs', verbose_name=_('email'))
    attach = models.FileField(_('attach'), upload_to='attachments')

    class Meta:
        verbose_name = _('email attachment')
        verbose_name_plural = _('email attachments')


class InvCode(models.Model):
    event = models.ForeignKey(Event, related_name='codes', verbose_name=_('event'))
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
    event = models.ForeignKey(Event, related_name='fields', verbose_name=_('event'))
    order = models.IntegerField(_('order'), default=0)
    type = models.CharField(_('type'), max_length=100, choices=FIELD_TYPES, default='text')
    label = models.CharField(_('label'), max_length=500)
    help_text = models.CharField(_('help text'), max_length=1000, blank=True, null=True)
    required = models.BooleanField(_('required'), default=False)
    options = models.CharField(_('options'), max_length=500,
                               help_text='comma separated values, only for select type',
                               blank=True, null=True)

    class Meta:
        ordering = ['order']
        verbose_name = _('ticket field')
        verbose_name_plural = _('ticket fields')

    def form_type(self):
        choices = ((i, i) for i in map(str.strip, self.options.split(',')))

        types = {
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
    contributors = models.ImageField(_('contributors'), upload_to='templcontributors', blank=True, null=True)
    links = models.CharField(_('links'), max_length=200, blank=True, null=True)
    info = models.TextField(_('info text'), blank=True, null=True)
    note = models.CharField(_('note'), max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = _('ticket template')
        verbose_name_plural = _('ticket templates')

    def get_absolute_url(self):
        return reverse('template_preview', kwargs={'id': self.id})

    def __str__(self):
        return self.name
