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
from events.models import Event
from events.models import Session
from events.models import Gate
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
        ctx['gate'] = self.request.session.get('gate', '')
        return ctx

    def post(self, request, *args, **kwargs):
        data = {'st': "right", 'extra': ''}
        order = request.POST.get('order', '')
        s = self.request.session.get('session', '')
        g = self.request.session.get('gate', '')
        try:
            ticket = Ticket.objects.get(order=order,
                                        confirmed=True,
                                        used=False)
        except:
            data['st'] = 'wrong'
            return HttpResponse(json.dumps(data), content_type="application/json")

        special = False
        valid_session = ticket.session_id == s

        if valid_session and g and ticket.gate_name != g:
            data['st'] = 'maybe'
            data['extra'] = _("%(session)s - Gate: %(gate)s") % {'session': ticket.session, 'gate': ticket.gate_name}
            return HttpResponse(json.dumps(data), content_type="application/json")

        if not valid_session: # checking extra
            extra = ticket.get_extra_session(s)
            if extra:
                if extra.get('used'):
                    data['st'] = 'wrong'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                start = datetime.strptime(extra.get('start'), settings.DATETIME_FORMAT)
                end = datetime.strptime(extra.get('end'), settings.DATETIME_FORMAT)
                if end < datetime.now():
                    data['st'] = 'wrong'
                    data['extra'] = _("Expired session: ") + str(extra.get('session'))
                elif start > datetime.now():
                    data['st'] = 'maybe'
                    data['extra'] = _("Wait 1.5h before for session") + str(extra.get('session'))
                else:
                    special = True
                    ticket.set_extra_session_to_used(s)
                    ticket.save()
            else:
                data['st'] = 'wrong'
                data['extra'] = str(ticket.session)

        if data['st'] == 'right' and not special:
            ticket.used = True
            ticket.save()

        return HttpResponse(json.dumps(data), content_type="application/json")
access = csrf_exempt(AccessView.as_view())


class AccessLogout(View):
    def get(self, request, ev, ac):
        auth_logout(request)
        return redirect('access', ev=ev, ac=ac)
access_logout = AccessLogout.as_view()
