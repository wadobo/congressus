from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse

from .models import TicketWindow
from tickets.views import MultiPurchaseView


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

    pass
    # TODO
    #   * auto confirm in the post
    #   * store ticketwindow related information after each purchase
    #   * post should return a downloadable PDF
window_multipurchase = WindowMultiPurchase.as_view()
