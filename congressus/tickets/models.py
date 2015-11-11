import random
from django.utils import timezone
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import get_template
from django.template import Context

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.urlresolvers import reverse


REG_TYPES = (
    ('invited', _('Invited')),
    ('speaker', _('Speaker')),
    ('regular', _('Regular')),
    ('student', _('Student'))
)

INV_TYPES = (
    ('invited', _('Invited')),
    ('speaker', _('Speaker')),
    ('student', _('Student'))
)

FOOD = (
    ('all', _('All')),
    ('vegetarian', _('Vegetarian')),
    ('vegan', _('Vegan'))
)

class Event(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'))
    price = models.IntegerField(_('ticket price'), default=25)
    price_student = models.IntegerField(_('student price'), default=25)
    price_speaker = models.IntegerField(_('speaker price'), default=0)
    price_invited = models.IntegerField(_('invited price'), default=0)
    info = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)
    admin = models.EmailField(_('admin email'), blank=True, null=True)
    max = models.IntegerField(_('max tickets'), default=300)

    class Meta:
        ordering = ['-start']

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


class InvCode(models.Model):
    event = models.ForeignKey(Event, related_name='codes')
    code = models.CharField(_('code'), max_length=10, blank=True, null=True)
    person = models.CharField(_('for person'), max_length=100, blank=True, null=True)
    used = models.BooleanField(_('used'), default=False)
    type = models.CharField(_('type'), choices=INV_TYPES, default='invited', max_length=15)

    def __str__(self):
        return "%s - %s" % (self.code, self.type)


class ConfirmEmail(models.Model):
    event = models.OneToOneField(Event, related_name='email')
    subject = models.CharField(_('subject'), max_length=300)
    body = models.TextField(_('body'))

    def __str__(self):
        return "ConfirmEmail - %s" % self.event


class EmailAttachment(models.Model):
    email = models.ForeignKey(ConfirmEmail, related_name='attachs')
    attach = models.FileField(_('attach'), upload_to='attachments')


class Ticket(models.Model):
    event = models.ForeignKey(Event, related_name='tickets')
    inv = models.OneToOneField(InvCode, blank=True, null=True)
    order = models.CharField(_('Order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('Order TPV'), max_length=12, blank=True, null=True)
    created = models.DateTimeField(_('Created at'), auto_now_add=True)

    confirmed_date = models.DateTimeField(_('Confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(default=False)
    confirm_sent = models.BooleanField(default=False)

    # Form Fields
    email = models.EmailField(_('Email'))
    name = models.CharField(_('Full name'), max_length=200)
    org = models.CharField(_('Organization'), max_length=200)

    type = models.CharField(_('Type'), max_length=20, choices=REG_TYPES, default='regular')
    food = models.CharField(_('Food preferences'), max_length=20, choices=FOOD, default='all')
    comments = models.TextField(_('Special needs'), blank=True, null=True)
    arrival = models.DateField(_('Arrival date'), help_text='dd/mm/YYYY')
    departure = models.DateField(_('Departure date'), help_text='dd/mm/YYYY')

    personal_info = ['email', 'name', 'org']
    reg_info = ['type', 'food', 'comments', 'arrival', 'departure']
    form_fields = personal_info + reg_info

    def get_absolute_url(self):
        return reverse('payment', kwargs={'order': self.order})

    def gen_order_tpv(self):
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.order_tpv = timezone.now().strftime('%y%m%d')
        self.order_tpv += ''.join(random.choice(chars) for _ in range(6))
        self.save()

    def get_personal_info(self):
        pinfo = []
        for f in self.personal_info:
            field = getattr(self, f)
            name = Ticket._meta.get_field_by_name(f)[0].verbose_name
            pinfo.append({'value': field, 'name': name, 'f': f})
        return pinfo

    def get_reg_info(self):
        pinfo = []
        for f in self.reg_info:
            field = getattr(self, f)
            name = Ticket._meta.get_field_by_name(f)[0].verbose_name
            pinfo.append({'value': field, 'name': name})
        return pinfo

    def get_price(self):
        price = self.event.price
        if self.type == 'speaker':
            price = self.event.price_speaker
        elif self.type == 'student':
            price = self.event.price_student
        elif self.type == 'invited':
            price = self.event.price_invited
        return price

    def send_reg_email(self):
        tmpl = get_template('emails/reg.txt')
        d = Context({'ticket': self})
        body = tmpl.render(d)
        email = EmailMessage(_('New Register / %s') % self.event.name,
                             body, settings.FROM_EMAIL, [self.event.admin])
        email.send(fail_silently=False)

    def send_confirm_email(self):
        # email to admin
        d = Context({'ticket': self})
        tmpl = get_template('emails/confirm.txt')
        body = tmpl.render(d)
        email = EmailMessage(_('Confirmed / %s') % self.event.name,
                             body, settings.FROM_EMAIL, [self.event.admin])
        email.send(fail_silently=False)

        # email to user
        e = self.event.get_email()
        if e:
            subject = e.subject
            body = e.body
        else:
            tmpl = get_template('emails/confirm-user.txt')
            subject = _('Ticket Confirmed / %s') % self.event.name
            body = tmpl.render(d)

        body = body.replace('TICKETID', self.order)

        email = EmailMessage(subject, body, settings.FROM_EMAIL, [self.email])

        if e:
            # adding attachments
            for att in e.attachs.all():
                email.attach_file(att.attach.path)

        email.send(fail_silently=False)

        self.confirm_sent = True
        self.save()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order


@receiver(post_save, sender=Ticket)
def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


@receiver(post_save, sender=InvCode)
def gencode(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.code:
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        instance.code = ''.join(random.choice(chars) for _ in range(10))
        instance.save()
