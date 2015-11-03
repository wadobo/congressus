import uuid
from django import forms
from .models import Ticket
from .models import InvCode
from .models import Event
from django.utils.translation import ugettext_lazy as _


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = Ticket.form_fields

    def __init__(self, *args, **kwargs):
        self.evid = kwargs.pop('evid')
        self.ev = Event.objects.get(id=self.evid)
        self.inv_code = None
        super(RegisterForm, self).__init__(*args, **kwargs)

    inv_code = forms.CharField(required=False, label=_("Invitation code"),
        widget=forms.TextInput(
        attrs={'placeholder':
               _("Add your invitation code, if you've one")}))

    def clean(self):
        data = super(RegisterForm, self).clean()
        inv_code = data.get('inv_code', '')
        type = data.get('type', '')
        if not inv_code:
            if type in ['speaker', 'invited']:
                raise forms.ValidationError(_("Invitation code is required for speaker or invited"))
            return data
        else:
            # checking invitation code
            if type not in ['speaker', 'invited']:
                raise forms.ValidationError(_("Invitation code is only for speaker or invited"))

            try:
                self.inv_code = InvCode.objects.get(event=self.ev, code=inv_code, used=False)
            except:
                raise forms.ValidationError(_("Invitation code invalid"))

        return data

    def save(self, *args, **kwargs):
        obj = super(RegisterForm, self).save(commit=False)
        obj.event = self.ev
        obj.order = str(uuid.uuid4())
        obj.gen_order_tpv()

        if self.inv_code:
            self.inv_code.used = True
            self.inv_code.save()
            obj.inv = self.inv_code

        obj.save()

        obj.send_reg_email()

        return obj
