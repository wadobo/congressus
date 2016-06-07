from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse

from .models import AccessControl
from events.models import Event

from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


class AccessLogin(TemplateView):
    template_name = 'windows/login.html'

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get('ev')
        ac = self.kwargs.get('ac')
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        ctx = super(AccessLogin, self).get_context_data(*args, **kwargs)
        ctx['ac'] = ac
        return ctx

    def post(self, request, ev=None, ac=None):
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            have_access = user.groups.filter(name='access').count()
            if user.is_active and have_access:
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
        return u.is_authenticated() and have_access

    def get_login_url(self):
        return reverse('access_login', kwargs=self.kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(AccessView, self).get_context_data(*args, **kwargs)
        ac = self.get_ac()
        ctx['ac'] = ac
        return ctx

    def post(self, request, *args, **kwargs):
        # TODO check access
        return render(request, self.template_name, ctx)
access = csrf_exempt(AccessView.as_view())


class AccessLogout(View):
    def get(self, request, ev, ac):
        auth_logout(request)
        return redirect('access', ev=ev, ac=ac)
access_logout = AccessLogout.as_view()
