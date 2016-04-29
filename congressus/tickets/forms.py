import uuid
from django import forms
from .models import Ticket

from events.models import Session, InvCode

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['email']

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session')
        self.inv = None

        super(RegisterForm, self).__init__(*args, **kwargs)

        # TODO add custom fields

    def clean(self):
        data = super(RegisterForm, self).clean()

        if not self.session.have_places():
            raise forms.ValidationError(_("Sorry, there's no more places for this event"))

        return data

    def save(self, *args, **kwargs):
        obj = super(RegisterForm, self).save(commit=False)
        obj.session = self.session
        obj.order = str(uuid.uuid4())
        obj.gen_order_tpv()

        if not obj.get_price():
            obj.confirmed = True
            obj.confirmed_date = timezone.now()
        obj.save()

        obj.send_reg_email()

        return obj
