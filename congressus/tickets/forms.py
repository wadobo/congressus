from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from events.models import Session
from tickets.models import MultiPurchase, Ticket


class RegisterForm(forms.ModelForm):
    confirm_email = forms.EmailField(label=_('Confirm email'),
            help_text=_("Enter the same email to confirm that it's well written"))

    class Meta:
        model = Ticket
        fields = ['email', 'confirm_email']

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session')
        self.inv = None

        super(RegisterForm, self).__init__(*args, **kwargs)

        for field in self.session.event().fields.all():
            self.fields[field.label] = field.form_type()

            if field.type == 'html':
                self.fields[field.label].label = False

        # Adding html5 required attr to required fields
        for f in self.fields.values():
            if f.required:
                f.widget.attrs['required'] = 'true'

    def clean(self):
        data = super(RegisterForm, self).clean()

        if self.request.user.is_admin:
            return data

        if not self.session.event().ticket_sale_enabled:
            raise forms.ValidationError(_("Ticket sale isn't enabled"))

        if not data['email'] == data['confirm_email']:
            raise forms.ValidationError(_("Emails didn't match"))

        if not self.session.have_places():
            raise forms.ValidationError(_("Sorry, there's no more places for this event"))

        return data

    def save(self, *args, **kwargs):
        obj = super(RegisterForm, self).save(commit=False)
        obj.session = self.session
        obj.gen_order()
        obj.gen_order_tpv()

        data = self.cleaned_data
        for field in self.session.event().fields.all():
            value = data.get(field.label, '')
            obj.set_extra_data(field.label, value)

        if not obj.get_price():
            obj.confirmed = True
            obj.confirmed_date = timezone.now()
        obj.fill_duplicated_data()
        obj.save()

        obj.send_reg_email()

        return obj


class MPRegisterForm(forms.ModelForm):
    confirm_email = forms.EmailField(label=_('Confirm email'),
            help_text=_("Enter the same email to confirm that it's well written"))

    class Meta:
        model = MultiPurchase
        fields = ['email', 'confirm_email']

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.ids = kwargs.pop('ids', [])
        self.seats = kwargs.pop('seats', [])
        self.client = kwargs.pop('client', '')

        super().__init__(*args, **kwargs)

        for field in self.event.fields.all():
            self.fields[field.label] = field.form_type()

            if field.type == 'html':
                self.fields[field.label].label = False

        # Adding html5 required attr to required fields
        for f in self.fields.values():
            if f.required:
                f.widget.attrs['required'] = 'true'

    def clean(self):
        if not self.event.ticket_sale_enabled:
            raise forms.ValidationError(_("Ticket sale isn't enabled"))

        data = super().clean()

        confirm_email = data.get('confirm_email', None)
        if confirm_email and not data.get('email') == confirm_email:
            raise forms.ValidationError(_("Emails didn't match"))

        tickets_without_seat = list(filter(lambda x: int(x[1]), self.ids))
        tickets_with_seat = list(filter(lambda x: bool(list(filter(None, x[1]))), self.seats))

        if not tickets_without_seat and not tickets_with_seat:
            raise forms.ValidationError(_("Select at least one ticket"))

        for sid, number in self.ids:
            n = int(number)
            if not n:
                continue
            session = Session.objects.get(id=sid)
            if n < 0 or n > settings.MAX_SEAT_BY_SESSION:
                raise forms.ValidationError(_("Sorry, you can't buy %(n)s tickets") %  {"n": n})
            if not session.have_places(n):
                raise forms.ValidationError(_("There's no %(n)s places for %(session)s") % {"n": n, "session": session})

        for sid, seats in self.seats:
            seats = list(filter(None, seats))
            if not seats:
                continue
            session = Session.objects.get(id=sid)
            for seat in seats:
                layout, row, column = seat.split('_')
                layout = session.space.seat_map.layouts.get(pk=layout)
                if not session.is_seat_available(layout, row, column, self.client):
                    s = row + '-' + column
                    raise forms.ValidationError(_("The seat %(seat)s is not available for %(session)s") % {"seat": s, "session": session})

        return data

    def save_seat_tickets(self, mp):
        # tickets with seat
        for sid, seats in self.seats:
            seats = list(filter(None, seats))
            if not seats:
                continue
            session = Session.objects.defer("space").get(id=sid)
            for seat in seats:
                layout, row, column = seat.split('_')
                layout = session.space.seat_map.layouts.get(pk=layout)
                # confirm_sent should be true to avoid multiple emails for
                # the same purchase
                t = Ticket(session=session, mp=mp, email=mp.email,
                           seat_layout=layout, seat=row + '-' + column,
                           confirm_sent=True)
                t.gen_order()
                t.fill_duplicated_data()
                t.save()

    def save_normal_tickets(self, mp):
        # tickets without seat
        for sid, number in self.ids:
            n = int(number)
            if not n:
                continue
            session = Session.objects.get(id=sid)
            for i in range(n):
                # confirm_sent should be true to avoid multiple emails for
                # the same purchase
                t = Ticket(session=session, mp=mp, email=mp.email,
                           confirm_sent=True)
                t.gen_order()
                t.fill_duplicated_data()
                t.save()

    def save_single_tickets(self, mp):
        self.save_normal_tickets(mp)
        self.save_seat_tickets(mp)
        return mp

    def save(self, *args, **kwargs):
        obj = super().save(commit=False)
        obj.ev = self.event
        obj.gen_order()
        obj.gen_order_tpv()

        data = self.cleaned_data
        for field in self.event.fields.all():
            value = data.get(field.label, '')
            obj.set_extra_data(field.label, value)
        obj.save()

        obj = self.save_single_tickets(obj)

        return obj
