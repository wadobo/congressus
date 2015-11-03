import hmac
import json
import uuid
from django.http import Http404, HttpResponse
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

from base64 import b64encode, b64decode
from pyDes import triple_des, CBC
from collections import OrderedDict
from hashlib import sha256


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


def tpv_sig_data(mdata, order, key, alt='+/'):
    k = b64decode(key.encode(), alt)
    x = triple_des(k, CBC, b"\0\0\0\0\0\0\0\0", pad='\0')
    okey = x.encrypt(order.encode())
    sig = hmac.new(okey, mdata.encode(), sha256).digest()
    sigb = b64encode(sig, alt).decode()
    return sigb


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
        ttype = '0'
        url = settings.TPV_MERCHANT_URL
        tpv_url = settings.TPV_URL
        terminal = settings.TPV_TERMINAL

        data = OrderedDict()
        data["DS_MERCHANT_AMOUNT"] = amount
        data["DS_MERCHANT_ORDER"] = order
        data["DS_MERCHANT_MERCHANTCODE"] = merchant
        data["DS_MERCHANT_CURRENCY"] = currency
        data["DS_MERCHANT_TRANSACTIONTYPE"] = ttype
        data["DS_MERCHANT_TERMINAL"] = terminal
        data["DS_MERCHANT_MERCHANTURL"] = url
        data["DS_MERCHANT_URLOK"] = settings.SITE_URL + '/ticket/%s/thanks/' % tk.order
        data["DS_MERCHANT_URLKO"] = ''

        jsdata = json.dumps(data).replace(' ', '')
        mdata = b64encode(jsdata.encode()).decode()

        sig = tpv_sig_data(mdata, order, key)

        ctx.update({
            'tpv_url': tpv_url,
            'mdata': mdata,
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
        mdata = request.POST.get('Ds_MerchantParameters', '')
        sig = request.POST.get('Ds_Signature', '')

        if not mdata or not sig:
            raise Http404

        jsdata = b64decode(mdata.encode(), b'-_').decode()
        data = json.loads(jsdata)
        order_tpv = data.get('Ds_Order', '')
        if not order_tpv:
            raise Http404

        sig2 = tpv_sig_data(mdata, order_tpv, settings.TPV_KEY, b'-_')
        if sig != sig2:
            raise Http404

        tk = get_object_or_404(Ticket, order_tpv=order_tpv)
        tk.confirmed = True
        tk.confirmed_date = timezone.now()
        tk.save()
        return HttpResponse("")
confirm = csrf_exempt(Confirm.as_view())
