import uuid
from hashlib import sha1
from django.conf import settings
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.views.generic.edit import ModelFormMixin
from django.views.generic import TemplateView
from django.views.generic import View

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from django.views.decorators.csrf import csrf_exempt

from django.utils.translation import ugettext as _

from .models import Ticket
from .models import Event
from .forms import RegisterForm


class Register(CreateView):
    model = Ticket
    form_class = RegisterForm

    def get_context_data(self, *args, **kwargs):
        ctx = super(Register, self).get_context_data(*args, **kwargs)
        evid = self.kwargs['evid']
        ev = get_object_or_404(Event, id=evid)
        ctx['ev'] = ev
        return ctx

    def get_form_kwargs(self):
        kwargs = super(Register, self).get_form_kwargs()
        kwargs['evid'] = self.kwargs['evid']
        return kwargs

    def get_success_url(self):
        '''
        Redirecting to TPV payment
        '''

        if not self.object.get_price():
            return reverse('thanks', kwargs={'order': self.object.order})

        return reverse('payment', kwargs={'order': self.object.order})
register = Register.as_view()


class Payment(TemplateView):
    template_name = 'tickets/payment.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(Payment, self).get_context_data(*args, **kwargs)
        tk = get_object_or_404(Ticket, order=kwargs['order'])
        ctx['ticket'] = tk

        if not tk.order_tpv:
            tk.gen_order_tpv()

        amount = str(tk.get_price() * 100)
        order = tk.order_tpv
        merchant = settings.TPV_MERCHANT
        currency = '978'
        key = settings.TPV_KEY

        msg = amount + order + merchant + currency + key
        sig = sha1(msg.encode()).hexdigest().upper()

        ctx.update({
            'amount': amount,
            'currency': currency,
            'order': order,
            'merchant': merchant,
            'terminal': settings.TPV_TERMINAL,
            'type': '0',
            'sig': sig,
        })

        return ctx
payment = Payment.as_view()


class Thanks(TemplateView):
    template_name = 'tickets/thanks.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(Thanks, self).get_context_data(*args, **kwargs)
        ctx['ticket'] = get_object_or_404(Ticket, order=kwargs['order'])
        return ctx
thanks = Thanks.as_view()


class Confirm(View):
    def post(self, request):
        order_tpv = request.POST.get('order_tpv', '????')
        tk = get_object_or_404(Ticket, order_tpv=order_tpv)
        tk.confirmed = True
        tk.confirmed_date = timezone.now()
        tk.save()
confirm = csrf_exempt(Confirm.as_view())
