from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from django.db.models.signals import post_save
from django.dispatch import receiver


INV_TYPES = (
    ('invited', _('Invited')),
    ('speaker', _('Speaker')),
    ('student', _('Student')),
)

FIELD_TYPES = (
    ('text', _('Text')),
    ('textarea', _('TextArea')),
    ('check', _('CheckBox')),
    ('select', _('Select')),
)


class Event(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)

    info = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)
    admin = models.EmailField(_('admin email'), blank=True, null=True)

    tshirt_img = models.ImageField(_('t-shirt img'), upload_to='tshirts',
                                   blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('register', kwargs={'id': self.id})

    def get_email(self):
        try:
            return self.email
        except:
            return None

    def sold(self):
        sold = self.tickets.filter(confirmed=True).count()
        return sold

    def get_type(self, t):
        from django.utils.translation import ugettext as _
        if t == 'invited':
            if not self.price_invited:
                return _('Invited (FREE, you need an invitation code)')
            return _('Invited (EUR %s, you need an invitation code)') % self.price_invited
        elif t == 'speaker':
            if not self.price_speaker:
                return _('Speaker (FREE, you need an invitation code)')
            return _('Speaker (EUR %s, you need an invitation code)') % self.price_speaker
        elif t == 'student':
            if not self.price_student:
                return _('Student (FREE, you need an invitation code)')
            return _('Student (EUR %s, you need an invitation code)') % self.price_student
        return _('Regular (EUR %s)') % self.price

    def get_sessions(self):
        sessions = []
        for space in self.spaces.all():
            sessions += list(space.sessions.all())
        return sessions


class Space(models.Model):
    event = models.ForeignKey(Event, related_name='spaces')
    name = models.CharField(_('name'), max_length=300)
    capacity = models.IntegerField(_('capacity'), default=100)
    numbered = models.BooleanField(_('numbered'), default=False)
    layout = models.TextField(_('seats layout'),
                              help_text=_('the layout to select the numbered seat'),
                              blank=True, null=True)

    def __str__(self):
        return '%s - %s' % (self.name, self.event)


class Session(models.Model):
    space = models.ForeignKey(Space, related_name='sessions')
    name = models.CharField(_('name'), max_length=300)

    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'))

    price = models.IntegerField(_('ticket price'), default=10)

    class Meta:
        ordering = ['-start']

    def __str__(self):
        return '%s - %s' % (self.name, self.space)


class ConfirmEmail(models.Model):
    event = models.OneToOneField(Event, related_name='email')
    subject = models.CharField(_('subject'), max_length=300)
    body = models.TextField(_('body'))

    def __str__(self):
        return "ConfirmEmail - %s" % self.event


class EmailAttachment(models.Model):
    email = models.ForeignKey(ConfirmEmail, related_name='attachs')
    attach = models.FileField(_('attach'), upload_to='attachments')


class InvCode(models.Model):
    event = models.ForeignKey(Event, related_name='codes')
    code = models.CharField(_('code'), max_length=10, blank=True, null=True)
    person = models.CharField(_('for person'), max_length=100, blank=True, null=True)
    used = models.BooleanField(_('used'), default=False)
    type = models.CharField(_('type'), choices=INV_TYPES, default='invited', max_length=15)

    def __str__(self):
        return "%s - %s" % (self.code, self.type)


class TicketField(models.Model):
    event = models.ForeignKey(Event, related_name='fields')
    type = models.CharField(max_length=100, choices=FIELD_TYPES, default='text')
    label = models.CharField(_('label'), max_length=100)
    help_text = models.CharField(_('help text'), max_length=200, blank=True, null=True)
    options = models.CharField(max_length=500,
                               help_text='comma separated values, only for select type',
                               blank=True, null=True)


@receiver(post_save, sender=InvCode)
def gencode(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.code:
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        instance.code = ''.join(random.choice(chars) for _ in range(10))
        instance.save()
