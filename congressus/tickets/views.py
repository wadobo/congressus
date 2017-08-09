import hmac
import json
import uuid
import random
import string
import operator

import redsystpv

from django.db.models import Count
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.template import Context
from django.template import Template
from django.utils import timezone
from django.utils import formats
from django.views.generic.edit import CreateView
from django.views.generic.edit import ModelFormMixin
from django.views.generic import TemplateView
from django.views.generic import View

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import UserPassesTestMixin

from django.views.decorators.csrf import csrf_exempt

from django.utils.translation import ugettext as _

from .models import Ticket
from .models import MultiPurchase
from .models import TicketSeatHold
from events.models import Session
from events.models import Event
from events.models import Space
from events.models import SeatMap
from events.models import SeatLayout

from windows.utils import online_sale

from .forms import RegisterForm
from .forms import MPRegisterForm
from tickets.utils import get_ticket_format
from tickets.utils import get_seats_by_str
from tickets.utils import search_seats
from invs.models import InvitationType

from base64 import b64encode, b64decode
from pyDes import triple_des, CBC
from collections import OrderedDict
from hashlib import sha256


class EventView(TemplateView):
    template_name = 'tickets/event.html'

    def get_context_data(self, *args, **kwargs):
        ev = get_object_or_404(Event, active=True, slug=self.kwargs['ev'])
        ctx = super(EventView, self).get_context_data(*args, **kwargs)
        ctx['ev'] = ev
        return ctx
event = EventView.as_view()


class LastEventView(View):
    def get(self, request):
        try:
            ev = Event.objects.filter(active=True)[0]
        except:
            raise Http404

        return redirect('multipurchase', ev=ev.slug)
last_event = LastEventView.as_view()


def seathold_update(client, type):
    """ Update client's seats hold, change type and reset date for avoid
    removed seat hold """
    for tsh in TicketSeatHold.objects.filter(Q(client=client), ~Q(type='R')):
        tsh.date = timezone.now()
        tsh.type = type
        tsh.save()


class MultiPurchaseView(TemplateView):
    template_name = 'tickets/multipurchase.html'

    def get_context_data(self, *args, **kwargs):
        ev = get_object_or_404(Event, active=True, slug=self.kwargs['ev'])
        ctx = super(MultiPurchaseView, self).get_context_data(*args, **kwargs)
        ctx['ev'] = ev

        # preloading seat layout data
        seat_maps = SeatMap.objects.filter(spaces__event=ev)
        ctx['seat_maps_table'] = {s.pk: s.get_table() for s in seat_maps}

        # preloading seat layout free seats number
        ctx['free_seats'] = {}
        q = TicketSeatHold.objects.filter(type="R").values('session', 'layout')
        q = q.annotate(busy=Count('pk'))
        q = q.values_list("session", "layout", "layout__layout", "busy")
        for s, l, layout, b in q:
            free = layout.count('L')
            ctx['free_seats'].update({(s, l): free - b})

        ctx['form'] = MPRegisterForm(event=ev)
        client = self.request.session.get('client', '')

        if not client:
            client = ''.join(random.choice(string.hexdigits) for _ in range(20))
            self.request.session['client'] = client

        authenticated_user = self.request.user.is_authenticated()
        if not authenticated_user:
            # Expired time reset. If not new client
            seathold_update(client, type='H')
            self.request.session.set_expiry(settings.EXPIRED_SEAT_H)

        ctx['client'] = client
        ctx['ws_server'] = settings.WS_SERVER
        ctx['max_seat_by_session'] = settings.MAX_SEAT_BY_SESSION
        ctx['is_windowsale'] = True if self.template_name != 'tickets/multipurchase.html' else False
        return ctx

    def post(self, request, ev=None):
        ev = get_object_or_404(Event, slug=ev)

        ids = [(i[len('number_'):], request.POST[i]) for i in request.POST if i.startswith('number_')]
        seats = [(i[len('seats_'):], request.POST[i].split(',')) for i in request.POST if i.startswith('seats_')]

        client = self.request.session.get('client', '')

        form = MPRegisterForm(request.POST,
                              event=ev, ids=ids, seats=seats,
                              client=client)

        if not client:
            expired = int(settings.EXPIRED_SEAT_H / 60)
            messages.error(request, _('Session has expired: you should'
                                      ' select seats again. Seats save'
                                      ' for you during {:d}'
                                      ' minutes.').format(expired))
            ctx = self.get_context_data()
            ctx['form'] = form
            ctx['session_expired'] = True
            return render(request, self.template_name, ctx)

        if form.is_valid():
            mp = form.save()
            mp.send_reg_email()

            if not mp.get_price():
                mp.confirm(method=None)
                online_sale(mp)
                return redirect('thanks', order=mp.order)

            # Expired time reset
            seathold_update(client, type='C')
            self.request.session.set_expiry(settings.EXPIRED_SEAT_C)
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


def tpv_parse_data(mdata, sig):
    if not mdata or not sig:
        return None

    jsdata = b64decode(mdata.encode(), b'-_').decode()
    data = json.loads(jsdata)
    return data


def get_ticket_or_404(**kwargs):
    try:
        tk = MultiPurchase.objects.get(**kwargs)
    except ObjectDoesNotExist:
        try:
            tk = Ticket.objects.get(**kwargs)
        except ObjectDoesNotExist:
            raise Http404
    return tk


class Payment(TemplateView):
    template_name = 'tickets/payment.html'

    def get_stripe_context(self, ctx, tk):
        # Disabled by default
        p = getattr(settings, 'STRIPE_ENABLED', False)
        if not p:
            return ctx

        ctx['stripe'] = {
            'pk': settings.STRIPE_PK,
            'amount': str(int(tk.get_price() * 100)),
            'name': settings.STRIPE_NAME,
            'desc': settings.STRIPE_DESC,
            'image': settings.STRIPE_IMAGE,
            'bitcoin': settings.STRIPE_BITCOIN,

        }
        return ctx

    def get_paypal_context(self, ctx, tk):
        # Disabled by default
        p = getattr(settings, 'PAYPAL_ENABLED', False)
        if not p:
            return ctx

        ctx['paypal'] = {
            'clientid': settings.PAYPAL_CLIENTID,
            'amount': '%5.2f' % tk.get_price(),
            'sandbox': settings.PAYPAL_SANDBOX,
        }
        return ctx

    def get_redsys_context(self, ctx, tk):
        # Enabled by default
        p = getattr(settings, 'REDSYS_ENABLED', True)
        if not p:
            return ctx

        amount = str(int(tk.get_price() * 100))
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
        data["DS_MERCHANT_CONSUMERLANGUAGE"] = settings.TPV_LANG
        data["DS_MERCHANT_URLOK"] = settings.SITE_URL + '/ticket/%s/thanks/' % tk.order
        data["DS_MERCHANT_URLKO"] = settings.SITE_URL + '/ticket/%s/payment/?error=1' % tk.order

        jsdata = json.dumps(data).replace(' ', '')
        mdata = b64encode(jsdata.encode()).decode()

        sig = tpv_sig_data(mdata, order, key)

        ctx.update({
            'redsys': True,
            'tpv_url': tpv_url,
            'mdata': mdata,
            'sig': sig,
        })

        return ctx

    def get_context_data(self, *args, **kwargs):
        ctx = super(Payment, self).get_context_data(*args, **kwargs)
        tk = get_ticket_or_404(order=kwargs['order'])
        ctx['ticket'] = tk
        ctx['error'] = self.request.GET.get('error', '')
        ctx['expired_time'] = settings.EXPIRED_SEAT_C

        ctx = self.get_redsys_context(ctx, tk)
        ctx = self.get_paypal_context(ctx, tk)
        ctx = self.get_stripe_context(ctx, tk)

        if not tk.confirmed and (not tk.order_tpv or ctx['error']):
            tk.gen_order_tpv()

        if not ctx['error']:
            expired = int(settings.EXPIRED_SEAT_C / 60)
            messages.info(self.request, _('You should complete the proccess'
                                          ' of payment in less than {:d}'
                                          ' minutes').format(expired))
        else:
            mdata = self.request.GET.get('Ds_MerchantParameters', '')
            sig = self.request.GET.get('Ds_Signature', '')
            data = tpv_parse_data(mdata, sig)

            if data and data['Ds_Response'] != '0000':
                resp = data['Ds_Response']
                error = redsystpv.ERROR_CODES.get(int(resp), _('Unknown error'))
                ctx['errormsg'] = '{}: {}'.format(resp, error)

        return ctx

    def post(self, request, order):
        tk = get_ticket_or_404(order=order)
        client = self.request.session.get('client', '')
        if not client:
            expired = int(settings.EXPIRED_SEAT_C / 60)
            messages.error(request, _('Session has expired: you should'
                                      ' confirm payment in less than'
                                      ' {:d} minutes. You need to select'
                                      ' seats again.').format(expired))
            return redirect('multipurchase', ev=tk.event().slug)

        # Expired time reset to expired_time_TPV
        seathold_update(client, type='P')
        self.request.session.set_expiry(settings.EXPIRED_SEAT_P)

        return JsonResponse({'status': 'ok'})

payment = csrf_exempt(Payment.as_view())


class Thanks(TemplateView):
    template_name = 'tickets/thanks.html'

    def post(self, request, order):
        ticket = get_ticket_or_404(order=request.POST.get('ticket'), confirmed=True)
        response = get_ticket_format(ticket, pf='A4')
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
        data = tpv_parse_data(mdata, sig)

        if not data:
            raise Http404

        order_tpv = data.get('Ds_Order', '')
        resp = data.get('Ds_Response', '')
        error = data.get('Ds_ErrorCode', '')
        if not order_tpv:
            raise Http404

        tk = get_ticket_or_404(order_tpv=order_tpv)

        if error or resp != '0000':
            # payment error
            err1, err2 = '', ''
            if resp != '0000':
                msg = redsystpv.ERROR_CODES.get(int(resp), _('Unknown error'))
                err1 = '{}: {}'.format(resp, msg)
            if error:
                msg = redsystpv.SIS_CODES.get(error, _('Unknown error'))
                err2 = '{}: {}'.format(error, msg)
            tk.set_error(err1, err2)
            raise Http404

        sig2 = tpv_sig_data(mdata, order_tpv, settings.TPV_KEY, b'-_')
        if sig != sig2:
            raise Http404

        tk.confirm()

        online_sale(tk)
        return HttpResponse("")
confirm = csrf_exempt(Confirm.as_view())


class ConfirmPaypal(View):
    def post(self, request):
        import paypalrestsdk

        paypalrestsdk.configure({
          'mode': 'sandbox',
          'client_id': settings.PAYPAL_CLIENTID,
          'client_secret': settings.PAYPAL_SECRET})

        payment_id = request.POST['payment_id']
        try:
            p = paypalrestsdk.Payment.find(payment_id)
        except:
            raise Http404

        tr = p.transactions[0]
        order_tpv = tr.invoice_number
        tk = get_ticket_or_404(order_tpv=order_tpv)

        if (float(tr.amount.total) == tk.get_price() and
                p.intent == 'sale' and p.state == 'approved'):
            tk.confirm(method="paypal")
            online_sale(tk)
        else:
            return JsonResponse({'status': 'error'})

        return JsonResponse({'status': 'ok'})
confirm_paypal = csrf_exempt(ConfirmPaypal.as_view())


class ConfirmStripe(View):
    def post(self, request, order):
        import stripe
        stripe.api_key = settings.STRIPE_SK

        token = request.POST['stripeToken']

        tk = get_ticket_or_404(order=order)
        amount = str(int(tk.get_price() * 100))
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='eur',
                source=token
            )
        except stripe.CardError as e:
            messages.error(request, _('The credit card has been declined.'))
            return redirect('payment', order=tk.order)

        tk.confirm(method="stripe")
        online_sale(tk)

        return redirect('thanks', order=tk.order)
confirm_stripe = ConfirmStripe.as_view()


class SeatView(TemplateView):
    template_name = 'tickets/seats.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(SeatView, self).get_context_data(*args, **kwargs)
        ctx['map'] = get_object_or_404(SeatMap, id=kwargs['map'])
        ctx['q'] = self.request.GET.get('q', '')
        return ctx
seats = SeatView.as_view()


class AutoSeats(View):
    def post(self, request):
        ctx = {'seats': []}
        req = request.POST
        session = req.get('session')
        amount = 0

        try:
            amount = int(req.get('amount_seats'))
        except:
            return HttpResponse(json.dumps(ctx), content_type="application/json")

        session = Session.objects.get(id=session)
        seats = search_seats(session, amount)
        if seats:
            ctx['seats'] = seats
        else:
            ctx['error'] = _("Not found contiguous seats, please, select manually using the green button")

        if not amount:
            ctx['fail_silently'] = True

        return HttpResponse(json.dumps(ctx), content_type="application/json")
autoseats = csrf_exempt(AutoSeats.as_view())


class AjaxLayout(TemplateView):
    template_name = 'tickets/layout.html'

    def get_context_data(self, session, layout, **kwargs):
        ctx = super(AjaxLayout, self).get_context_data(**kwargs)
        layout = get_object_or_404(SeatLayout, id=layout)
        session = get_object_or_404(Session, id=session)
        ctx['layout'] = layout
        ctx['session'] = session
        return ctx
ajax_layout = AjaxLayout.as_view()


class TicketTemplatePreview(UserPassesTestMixin, View):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated() and u.is_superuser

    def get(self, request, id):
        from events.models import TicketTemplate
        template = get_object_or_404(TicketTemplate, pk=id)

        # fake ticket
        ticket = Ticket(email='test@email.com', price=12, tax=21, confirm_sent=True)
        ticket.gen_order(save=False)
        ticket.created = timezone.now()

        ticket.session = Session(
                          name=formats.date_format(timezone.now(), "l"),
                          template=template,
                          space=random.choice(list(Space.objects.all())),
                          start=timezone.now(),
                          end=timezone.now())

        response = get_ticket_format(ticket, pf='A4', attachment=False)
        return response

template_preview = TicketTemplatePreview.as_view()


class ThermalTicketTemplatePreview(TicketTemplatePreview):
    def get(self, request, id):
        from events.models import ThermalTicketTemplate
        template = get_object_or_404(ThermalTicketTemplate, pk=id)

        # fake ticket
        ticket = Ticket(email='test@email.com', price=12, tax=21, confirm_sent=True)
        ticket.gen_order(save=False)
        ticket.created = timezone.now()

        ticket.session = Session(
                          name=formats.date_format(timezone.now(), "l"),
                          thermal_template=template,
                          space=random.choice(list(Space.objects.all())),
                          start=timezone.now(),
                          end=timezone.now())

        response = get_ticket_format(ticket, pf='thermal', attachment=False)
        return response
thermal_template_preview = ThermalTicketTemplatePreview.as_view()


class EmailConfirmPreview(UserPassesTestMixin, View):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated() and u.is_superuser

    def get(self, request, id):
        from events.models import ConfirmEmail
        email_confirm = get_object_or_404(ConfirmEmail, pk=id)

        event = Event.objects.filter(email=email_confirm).first()
        if event:
            # fake ticket
            ticket = Ticket(email='test@email.com', price=12, tax=21,  confirm_sent=True)
            ticket.gen_order(save=False)
            ticket.created = timezone.now()

            ticket.session = Session(
                              name=formats.date_format(timezone.now(), "l"),
                              #template=template,
                              space=random.choice(list(Space.objects.all())),
                              start=timezone.now(),
                              end=timezone.now())

            extra = json.loads(ticket.extra_data)
            subject = Template(event.email.subject).render(Context({'ticket': ticket, 'extra': extra}))
            body = Template(event.email.body).render(Context({'ticket': ticket, 'extra': extra}))
            sname = _("SUBJECT")
            bname = _("BODY")
            email = "%s:\n%s\n\n%s:\n%s" % (sname, subject, bname, body)
        else:
            email = _("You should assing this email_confirm to some events.")
        response = HttpResponse(email, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="email.txt"'
        return response

email_confirm_preview = EmailConfirmPreview.as_view()


class SeatsByStr(View):
    def post(self, request):
        ctx = {}
        invi_type_id = request.POST.get('invi_type')
        if invi_type_id:
            invi_type = get_object_or_404(InvitationType, id=invi_type_id)
            sessions = invi_type.sessions.all()
            string = request.POST.get('string', '')
            try:
                dic = get_seats_by_str(sessions, string)
                total = 0
                for val in dic.values():
                    total += len(val)
                ctx['total'] = total
                ctx['values'] = dic.__str__()
            except:
                ctx['error'] = 'invalid'
        else:
            ctx['error'] = _('neccessary select invitation type')
        return JsonResponse(ctx)
seats_by_str = csrf_exempt(SeatsByStr.as_view())


def csrf_failure(request, reason=""):
    messages.error(request, _('Session error, send again the form'))
    return redirect(request.path or 'last_event')
