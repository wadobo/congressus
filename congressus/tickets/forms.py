import uuid
from django import forms
from .models import Ticket
from .models import MultiPurchase

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

        for field in self.session.event().fields.all():
            self.fields[field.label] = field.form_type()

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
    class Meta:
        model = MultiPurchase
        fields = ['email']

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.ids = kwargs.pop('ids', [])
        self.seats = kwargs.pop('seats', [])

        super(MPRegisterForm, self).__init__(*args, **kwargs)

        for field in self.event.fields.all():
            self.fields[field.label] = field.form_type()

    def clean(self):
        data = super(MPRegisterForm, self).clean()

        for sid, number in self.ids:
            session = Session.objects.get(space__event=self.event, id=sid)
            n = int(number)
            if n < 0 or n > 10:
                raise forms.ValidationError(_("Sorry, you can't buy %s tickets") % n)
            if not session.have_places(n):
                raise forms.ValidationError(_("There's no %s places for %s") % (n, session))

        for sid, seats in self.seats:
            session = Session.objects.get(space__event=self.event, id=sid)
            for seat in seats:
                layout, row, column = seat.split('_')
                layout = session.space.seat_map.layouts.get(pk=layout)
                if not session.is_seat_available(layout, row, column):
                    s = row + '-' + column
                    raise forms.ValidationError(_("The seat %s is not available for %s") % (s, session))

        return data

    def save_seat_tickets(self, mp):
        # tickets with seat
        for sid, seats in self.seats:
            session = Session.objects.get(space__event=self.event, id=sid)
            for seat in seats:
                layout, row, column = seat.split('_')
                layout = session.space.seat_map.layouts.get(pk=layout)
                order = str(uuid.uuid4())
                # confirm_sent should be true to avoid multiple emails for
                # the same purchase
                t = Ticket(session=session, mp=mp, email=mp.email,
                           seat_layout=layout, seat=row + '-' + column,
                           confirm_sent=True, order=order)
                t.fill_duplicated_data()
                t.save()

    def save_normal_tickets(self, mp):
        # tickets without seat
        for sid, number in self.ids:
            session = Session.objects.get(space__event=self.event, id=sid)
            n = int(number)
            for i in range(n):
                order = str(uuid.uuid4())
                # confirm_sent should be true to avoid multiple emails for
                # the same purchase
                t = Ticket(session=session, mp=mp, email=mp.email,
                           confirm_sent=True, order=order)
                t.fill_duplicated_data()
                t.save()

    def save_single_tickets(self, mp):
        self.save_normal_tickets(mp)
        self.save_seat_tickets(mp)
        return mp

    def save(self, *args, **kwargs):
        obj = super(MPRegisterForm, self).save(commit=False)
        obj.ev = self.event
        obj.order = str(uuid.uuid4())
        obj.gen_order_tpv()

        data = self.cleaned_data
        for field in self.event.fields.all():
            value = data.get(field.label, '')
            obj.set_extra_data(field.label, value)
        obj.save()

        obj = self.save_single_tickets(obj)

        return obj
