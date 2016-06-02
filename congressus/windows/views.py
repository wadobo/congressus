from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse

from .models import TicketWindow
from tickets.views import MultiPurchaseView
from events.models import Event
from tickets.forms import MPRegisterForm

from django.contrib.auth import logout as auth_logout


class WindowLogin(TemplateView):
    template_name = 'windows/login.html'

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get('ev')
        w = self.kwargs.get('w')
        w = get_object_or_404(TicketWindow, event__slug=ev, slug=w)
        ctx = super(WindowLogin, self).get_context_data(*args, **kwargs)
        ctx['window'] = w
        return ctx

    def post(self, request, ev=None, w=None):
        w = get_object_or_404(TicketWindow, event__slug=ev, slug=w)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active and w.users.filter(id=user.id).count():
                login(request, user)
                return redirect('window_multipurchase', ev=w.event.slug, w=w.slug)
            else:
                messages.error(request, _("This user can't access in this ticket window"))
        else:
            messages.error(request, _("Invalid username or password"))

        return render(request, self.template_name,
                      self.get_context_data(ev=ev, w=w.slug))
window_login = WindowLogin.as_view()


class WindowMultiPurchase(UserPassesTestMixin, MultiPurchaseView):
    template_name = 'windows/multipurchase.html'

    def get_window(self):
        ev = self.kwargs['ev']
        w = self.kwargs['w']
        w = get_object_or_404(TicketWindow, event__slug=ev, slug=w)
        return w

    def test_func(self):
        u = self.request.user
        w = self.get_window()
        return u.is_authenticated() and w.users.filter(id=u.id).count()

    def get_login_url(self):
        return reverse('window_login', kwargs=self.kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(WindowMultiPurchase, self).get_context_data(*args, **kwargs)
        w = self.get_window()
        ctx['window'] = w
        ctx['subsum'] = True
        return ctx

    def post(self, request, *args, **kwargs):
        w = self.get_window()

        ids = [(i[len('number_'):], request.POST[i]) for i in request.POST if i.startswith('number_')]
        seats = [(i[len('seats_'):], request.POST[i].split(',')) for i in request.POST if i.startswith('seats_')]

        form = MPRegisterForm(request.POST,
                              event=w.event, ids=ids, seats=seats,
                              client=request.session.get('client', ''))
        form.fields = {}
        # TODO add the ticket email to the mp before save
        if form.is_valid():
            mp = form.save()
            mp.confirm()
            # TODO return the downloadable ticket PDF
            # TODO store ticketwindow related information after each purchase

        ctx = self.get_context_data()
        ctx['form'] = form

        return render(request, self.template_name, ctx)
window_multipurchase = WindowMultiPurchase.as_view()


class WindowLogout(View):
    def get(self, request, ev, w):
        auth_logout(request)
        return redirect('window_multipurchase', ev=ev, w=w)
window_logout = WindowLogout.as_view()
