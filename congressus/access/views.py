import json
from datetime import datetime
from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext as _
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


class AccessLogin(TemplateView):
    template_name = 'access/login.html'

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get('ev')
        ac = self.kwargs.get('ac')
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        ctx = super(AccessLogin, self).get_context_data(*args, **kwargs)
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

    def response_json(self, msg, st='right'):
        data = {}
        data['st'] = st
        data['extra'] = msg
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
            return 'maybe', str(ticket.session)

        if extra.get('used'):
            return 'wrong', _('Used')

        start = datetime.strptime(extra.get('start'), settings.DATETIME_FORMAT)
        end = datetime.strptime(extra.get('end'), settings.DATETIME_FORMAT)

        if end < datetime.now():
            msg = _("Expired session: ") + str(extra.get('session'))
            return 'wrong', msg
        elif start >= datetime.now():
            msg = _("Too soon: ") + str(extra.get('session'))
            return 'wrong', msg

        ticket.set_extra_session_to_used(s)
        ticket.save()

        return 'right', str(ticket.session)

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
        valid_gate = ticket.gate_name is None or ticket.gate_name == g

        if ticket.used:
            msg = _('Used')
            return self.response_json(msg, st='wrong')

        elif not valid_session:
            # check if this has an extra session
            st, msg = self.check_extra_session(ticket, s)
            return self.response_json(msg, st=st)

        elif not valid_gate:
            msg = _("%(session)s - Gate: %(gate)s") % {'session': ticket.session, 'gate': ticket.gate_name}
            return self.response_json(msg, st='maybe')

        ticket.used = True
        ticket.save()
        msg = str(ticket.session)
        return self.response_json(msg)
access = csrf_exempt(AccessView.as_view())


class AccessLogout(View):
    def get(self, request, ev, ac):
        auth_logout(request)
        return redirect('access', ev=ev, ac=ac)
access_logout = AccessLogout.as_view()
