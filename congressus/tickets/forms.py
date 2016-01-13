import uuid
from django import forms
from .models import Ticket
from .models import InvCode
from .models import Event
from .models import SHIRT_TYPES
from .models import TShirt
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = Ticket.form_fields

    def __init__(self, *args, **kwargs):
        self.evid = kwargs.pop('evid')
        self.ev = Event.objects.get(id=self.evid)
        self.inv = None

        c = kwargs.pop('captcha')
        cs = kwargs.pop('captcha_solution')
        super(RegisterForm, self).__init__(*args, **kwargs)

        choices = self.fields['type'].widget.choices
        for i in range(len(choices)):
            current = choices[i]
            choices[i] = (current[0], self.ev.get_type(current[0]))

        cp = self.fields['captcha']
        cp.help_text = c
        self.captcha_solution = cs

    tshirt = forms.CharField(required=True, label=_("T-Shirt size"),
        widget=forms.Select(choices=SHIRT_TYPES))

    inv_code = forms.CharField(required=False, label=_("Invitation code"),
        widget=forms.TextInput(
        attrs={'placeholder':
               _("Only for Student, Invited and Speaker")}))
    captcha = forms.CharField(required=True, label=_("Captcha"),
        help_text="3+2",
        widget=forms.TextInput(
        attrs={'placeholder':
               _('Result, for example for "3 - 2" write "1"')}))

    idx = Ticket.form_fields.index('comments') + 1
    field_order = (Ticket.form_fields[0:idx] + ['tshirt'] +
                   Ticket.form_fields[idx:] + ['inv_code', 'captcha'])

    def clean_captcha(self):
        c = self.cleaned_data['captcha']
        try:
            c = int(c)
        except:
            raise forms.ValidationError(_("Captcha is incorrect"))

        if not c == self.captcha_solution:
            raise forms.ValidationError(_("Captcha is incorrect"))
        return c

    def clean(self):
        data = super(RegisterForm, self).clean()
        inv_code = data.get('inv_code', '')
        type = data.get('type', '')

        if self.ev.sold() >= self.ev.max:
            raise forms.ValidationError(_("Sorry, there's no more places for this event"))

        if not inv_code:
            if type in ['student', 'speaker', 'invited']:
                raise forms.ValidationError(_("Invitation code is required for student, speaker or invited"))
            return data
        else:
            # checking invitation code
            if type not in ['student', 'speaker', 'invited']:
                raise forms.ValidationError(_("Invitation code is only for student, speaker or invited"))

            try:
                self.inv = InvCode.objects.get(event=self.ev, code=inv_code, type=type, used=False)
            except:
                raise forms.ValidationError(_("Invitation code invalid"))

        return data

    def save(self, *args, **kwargs):
        obj = super(RegisterForm, self).save(commit=False)
        obj.event = self.ev
        obj.order = str(uuid.uuid4())
        obj.gen_order_tpv()

        if self.inv:
            self.inv.used = True
            self.inv.save()
            obj.inv = self.inv
            obj.confirmed = True
            obj.confirmed_date = timezone.now()
        obj.save()

        obj.send_reg_email()

        tshirt = self.cleaned_data['tshirt']
        tshirt = TShirt(ticket=obj, size=tshirt)
        tshirt.save()

        return obj


class TShirtForm(forms.ModelForm):
    class Meta:
        model = TShirt
        fields = ['size']

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        self.ticket = Ticket.objects.get(order=self.order)

        super(TShirtForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        ts, created = TShirt.objects.get_or_create(ticket=self.ticket)
        ts.size = self.cleaned_data['size']
        ts.save()
        return ts
