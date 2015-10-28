import uuid
from django.conf import settings
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.views.generic.edit import ModelFormMixin
from django.views.generic import TemplateView
from django.views.generic import View

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from .models import Ticket
from .models import Event


class Register(CreateView):
    model = Ticket
    fields = Ticket.form_fields

    def get_context_data(self, *args, **kwargs):
        ctx = super(Register, self).get_context_data(*args, **kwargs)
        evid = self.kwargs['evid']
        ev = get_object_or_404(Event, id=evid)
        ctx['ev'] = ev
        return ctx

    def form_valid(self, form):
        evid = self.kwargs['evid']
        ev = get_object_or_404(Event, id=evid)
        self.object = form.save(commit=False)
        self.object.event = ev
        self.object.order = str(uuid.uuid4())
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)

    def get_success_url(self):
        '''
        Redirecting to TPV payment
        '''
        return reverse('payment', kwargs={'order': self.object.order})
register = Register.as_view()


class Payment(TemplateView):
    template_name = 'tickets/payment.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(Payment, self).get_context_data(*args, **kwargs)
        ctx['ticket'] = get_object_or_404(Ticket, order=kwargs['order'])
        return ctx
payment = Payment.as_view()


class Thanks(TemplateView):
    template_name = 'tickets/thanks.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(Thanks, self).get_context_data(*args, **kwargs)
        ctx['ticket'] = get_object_or_404(Ticket, order=kwargs['order'])
        return ctx
thanks = Thanks.as_view()
