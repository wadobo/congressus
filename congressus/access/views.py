import json
from datetime import datetime
from datetime import timedelta
from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.utils import formats
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse

from .models import AccessControl
from .models import LogAccessControl
from events.models import Event
from events.models import Session
from events.models import Gate
from tickets.models import Invitation
from tickets.models import Ticket

from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


def short_date(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return formats.date_format(dt, 'SHORT_DATETIME_FORMAT')


class AccessLogin(TemplateView):
    template_name = 'access/login.html'

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get('ev')
        ac = self.kwargs.get('ac')
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        ctx = super(AccessLogin, self).get_context_data(*args, **kwargs)
        ctx['ev'] = ac.event
        ctx['ac'] = ac
        ctx['sessions'] = ac.event.get_sessions()
        ctx['gates'] = ac.event.gates.all()
        return ctx

    def post(self, request, ev=None, ac=None):
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            have_access = user.groups.filter(name='access').count()
            if user.is_active and have_access:
                # session
                session = get_object_or_404(Session,
                            space__event__slug=ev,
                            id=request.POST['session'])
                request.session['session'] = session.id
                # gate
                gate = request.POST.get('gate', '')
                if gate:
                    gate = get_object_or_404(Gate, event__slug=ev,
                                id=gate)
                    request.session['gate'] = gate.name
                else:
                    request.session['gate'] = ''
                login(request, user)
                return redirect('access', ev=ac.event.slug, ac=ac.slug)
            else:
                messages.error(request, _("This user can't access in this access control"))
        else:
            messages.error(request, _("Invalid username or password"))

        return render(request, self.template_name,
                      self.get_context_data(ev=ev, ac=ac.slug))
access_login = AccessLogin.as_view()


class AccessView(UserPassesTestMixin, TemplateView):
    template_name = 'access/access.html'

    def get_ac(self):
        ev = self.kwargs['ev']
        ac = self.kwargs['ac']
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        return ac

    def test_func(self):
        u = self.request.user
        have_access = u.groups.filter(name='access').count()
        have_access = have_access and 'session' in self.request.session
        have_access = have_access and 'gate' in self.request.session

        return u.is_authenticated() and have_access

    def get_login_url(self):
        return reverse('access_login', kwargs=self.kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(AccessView, self).get_context_data(*args, **kwargs)
        ac = self.get_ac()
        ctx['ac'] = ac
        s = Session.objects.get(id=self.request.session.get('session', ''))
        ctx['session'] = s
        ctx['ws_server'] = settings.WS_SERVER
        ctx['gate'] = self.request.session.get('gate', '')
        return ctx

    def get_order_type(self, order):
        if order.startswith(Invitation.ORDER_START):
            obj = Invitation
        else:
            obj = Ticket
        return obj

    def response_json(self, msg, msg2='', st='right'):
        data = {}
        data['st'] = st
        data['extra'] = msg
        data['extra2'] = msg2
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_ticket(self, order):
        obj = self.get_order_type(order)
        if obj == Ticket:
            return obj.objects.get(order=order, confirmed=True)
        else:
            return obj.objects.get(order=order)

    def check_extra_session(self, ticket, s):
        extra = ticket.get_extra_session(s)

        if not extra:
            return 'wrong', ticket.session.short()

        if extra.get('used'):
            used_date = datetime.strptime(extra['used_date'], settings.DATETIME_FORMAT)
            msg = _('Used: %(date)s') % {'date': short_date(used_date)}
            return 'wrong', msg

        start = datetime.strptime(extra['start'], settings.DATETIME_FORMAT)
        end = datetime.strptime(extra['end'], settings.DATETIME_FORMAT)
        session = Session.objects.get(pk=extra['session'])

        start_formatted = short_date(start)
        end_formatted = short_date(end)

        if end < datetime.now():
            msg = _("Expired, ended at %(date)s") % { 'date': end_formatted }
            return 'wrong', msg
        elif start > datetime.now():
            msg = _("Too soon, wait until %(date)s") % { 'date': start_formatted }
            return 'wrong', msg

        ticket.set_extra_session_to_used(s)
        ticket.save()

        return 'right', _('Extra session: %(session)s') % { 'session': session.short() }

    def post(self, request, *args, **kwargs):
        data = {'st': "right", 'extra': ''}
        order = request.POST.get('order', '')
        s = self.request.session.get('session', '')
        g = self.request.session.get('gate', '')

        # Checking order:
        #  * Check if the ticket exists
        #  * Check if it's used
        #  * Check if it's a valid session
        #    * check if there's extra session in this ticket
        #  * Check if it's a valid gate
        #  * If is a valid ticket, mark as used

        # TODO add ticket checked info to the msg

        try:
            ticket = self.get_ticket(order)
        except:
            return self.response_json(_('Not exists'), st='wrong')

        valid_session = ticket.session_id == s
        invalid_gate = (g and ticket.gate_name and ticket.gate_name != g)

        if ticket.used:
            msg = _('Used: %(date)s') % {'date': short_date(ticket.used_date)}
            return self.response_json(msg, msg2=str(ticket.session), st='wrong')

        if not valid_session:
            # check if this has an extra session
            st, msg = self.check_extra_session(ticket, s)
            return self.response_json(msg, msg2=str(ticket.session), st=st)

        if invalid_gate:
            data = { 'session': ticket.session.short(),
                     'gate': ticket.gate_name }
            msg = _("%(session)s - Gate: %(gate)s") % data
            return self.response_json(msg, st='maybe')

        # if we're here, everything is ok
        ticket.used = True
        ticket.used_date = timezone.now()
        ticket.save()
        msg = _("Ok: %(session)s") % { 'session': ticket.session.short() }
        return self.response_json(msg, msg2=ticket.order)
access = csrf_exempt(AccessView.as_view())


class AccessLogout(View):
    def get(self, request, ev, ac):
        auth_logout(request)
        return redirect('access', ev=ev, ac=ac)
access_logout = AccessLogout.as_view()


class AccessList(UserPassesTestMixin, TemplateView):
    template_name = 'access/list.html'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated() and u.is_superuser

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get('ev')
        ev = get_object_or_404(Event, slug=ev)
        ctx = super(AccessList, self).get_context_data(*args, **kwargs)
        ctx['access'] = ev.access.all()
        ctx['ev'] = ev

        ctx['date'] = timezone.now()

        d = self.request.GET.get('date', '')
        if d:
            date = datetime(*map(int, d.split('-')))
            ctx['date'] = date

        days = []
        d = timezone.now() - timedelta(10)
        d1 = timezone.now() + timedelta(10)
        while d < d1:
            days.append(d)
            d = d + timedelta(1)
        ctx['days'] = days
        ctx['today'] = timezone.now()
        ctx['menuitem'] = 'access'

        return ctx
access_list = AccessList.as_view()
