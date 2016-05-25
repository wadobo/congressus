import hmac
import json
import uuid
import random
import operator

from django.core.exceptions import ObjectDoesNotExist

from django.http import Http404, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.views.generic.edit import ModelFormMixin
from django.views.generic import TemplateView
from django.views.generic import View

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse

from django.views.decorators.csrf import csrf_exempt

from django.utils.translation import ugettext as _

from .models import Ticket
from .models import MultiPurchase
from events.models import Session
from events.models import Event
from events.models import Space
from events.models import SeatMap

from .forms import RegisterForm
from .forms import MPRegisterForm

from base64 import b64encode, b64decode
from pyDes import triple_des, CBC
from collections import OrderedDict
from hashlib import sha256


class EventView(TemplateView):
    template_name = 'tickets/event.html'

    def get_context_data(self, *args, **kwargs):
        ev = get_object_or_404(Event, slug=self.kwargs['ev'])
        ctx = super(EventView, self).get_context_data(*args, **kwargs)
        ctx['ev'] = ev
        return ctx
event = EventView.as_view()


class MultiPurchaseView(TemplateView):
    template_name = 'tickets/multipurchase.html'

    def get_context_data(self, *args, **kwargs):
        ev = get_object_or_404(Event, slug=self.kwargs['ev'])
        ctx = super(MultiPurchaseView, self).get_context_data(*args, **kwargs)
        ctx['ev'] = ev
        ctx['form'] = MPRegisterForm(event=ev)
        ctx['ws_server'] = 'localhost:9007'
        return ctx

    def post(self, request, ev=None):
        ev = get_object_or_404(Event, slug=ev)

        ids = [(i[len('number_'):], request.POST[i]) for i in request.POST if i.startswith('number_')]
        seats = [(i[len('seats_'):], request.POST[i].split(',')) for i in request.POST if i.startswith('seats_')]

        form = MPRegisterForm(request.POST, event=ev, ids=ids, seats=seats)
        if form.is_valid():
            mp = form.save()
            mp.send_reg_email()

            if not mp.get_price():
                mp.confirm()
                return redirect('thanks', order=mp.order)
            return redirect('payment', order=mp.order)

        ctx = self.get_context_data()
        ctx['form'] = form

        return render(request, self.template_name, ctx)
multipurchase = MultiPurchaseView.as_view()


class Register(CreateView):
    model = Ticket
    form_class = RegisterForm

    def get_context_data(self, *args, **kwargs):
        ctx = super(Register, self).get_context_data(*args, **kwargs)
        ev = self.kwargs['ev']
        sp = self.kwargs['space']
        se = self.kwargs['session']

        session = get_object_or_404(Session, slug=se,
                                    space__slug=sp,
                                    space__event__slug=ev)
        ctx['session'] = session
        return ctx

    def get_form_kwargs(self):
        kwargs = super(Register, self).get_form_kwargs()

        ev = self.kwargs['ev']
        sp = self.kwargs['space']
        se = self.kwargs['session']

        session = get_object_or_404(Session, slug=se,
                                    space__slug=sp,
                                    space__event__slug=ev)

        kwargs['session'] = session
        return kwargs

    def get_success_url(self):
        '''
        Redirecting to TPV payment
        '''

        if not self.object.get_price():
            return reverse('thanks', kwargs={'order': self.object.order})

        return reverse('payment', kwargs={'order': self.object.order})
register = Register.as_view()


def tpv_sig_data(mdata, order, key, alt=b'+/'):
    k = b64decode(key.encode(), alt)
    x = triple_des(k, CBC, b"\0\0\0\0\0\0\0\0", pad='\0')
    okey = x.encrypt(order.encode())
    sig = hmac.new(okey, mdata.encode(), sha256).digest()
    sigb = b64encode(sig, alt).decode()
    return sigb


def get_ticket_or_404(**kwargs):
    try:
        tk = Ticket.objects.get(**kwargs)
    except ObjectDoesNotExist:
        try:
            tk = MultiPurchase.objects.get(**kwargs)
        except ObjectDoesNotExist:
            raise Http404
    return tk


class Payment(TemplateView):
    template_name = 'tickets/payment.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(Payment, self).get_context_data(*args, **kwargs)
        tk = get_ticket_or_404(order=kwargs['order'])
        ctx['ticket'] = tk
        ctx['error'] = self.request.GET.get('error', '')

        if not tk.confirmed and (not tk.order_tpv or ctx['error']):
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
        data["DS_MERCHANT_CONSUMERLANGUAGE"] = '002'
        data["DS_MERCHANT_URLOK"] = settings.SITE_URL + '/ticket/%s/thanks/' % tk.order
        data["DS_MERCHANT_URLKO"] = settings.SITE_URL + '/ticket/%s/payment/?error=1' % tk.order

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

    def post(self, request, order):
        from reportlab.pdfgen import canvas
        ticket = Ticket.objects.get(order=request.POST.get('ticket'), confirmed=True)
        pdf = ticket.gen_pdf()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="tickets.pdf"'
        response.write(pdf)
        return response

    def get_context_data(self, *args, **kwargs):
        ctx = super(Thanks, self).get_context_data(*args, **kwargs)
        ctx['ticket'] = get_ticket_or_404(order=kwargs['order'], confirmed=True)
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
        resp = data.get('Ds_Response', '')
        error = data.get('Ds_ErrorCode', '')
        if not order_tpv:
            raise Http404

        if error or resp != '0000':
            # payment error
            raise Http404

        sig2 = tpv_sig_data(mdata, order_tpv, settings.TPV_KEY, b'-_')
        if sig != sig2:
            raise Http404

        tk = get_ticket_or_404(order_tpv=order_tpv)
        tk.confirm()
        return HttpResponse("")
confirm = csrf_exempt(Confirm.as_view())


class SeatView(TemplateView):
    template_name = 'tickets/seats.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(SeatView, self).get_context_data(*args, **kwargs)
        ctx['map'] = get_object_or_404(SeatMap, id=kwargs['map'])
        ctx['q'] = self.request.GET.get('q', '')
        return ctx
seats = SeatView.as_view()
