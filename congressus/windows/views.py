from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login

from .models import TicketWindow


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
        # TODO custom login
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active and w.users.find(user=user):
                login(request, user)
                # TODO Redirect to a success page.
                pass
            else:
                # TODO Return a 'disabled account' error message
                pass
        else:
            # TODO Return an 'invalid login' error message.
            pass

        return render(request, self.template_name, ctx)
window_login = WindowLogin.as_view()
