from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from events.models import Event

from .models import Invitation
from .models import InvitationType


class GenInvitationsView(UserPassesTestMixin, TemplateView):
    template_name = 'invs/generator.html'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated() and u.is_superuser

    def get_context_data(self, *args, **kwargs):
        ctx = super(GenInvitationsView, self).get_context_data(*args, **kwargs)
        ev = get_object_or_404(Event, slug=self.kwargs['ev'])
        ctx['ev'] = ev
        ctx['types'] = InvitationType.objects.all()
        ctx['menuitem'] = 'inv'
        return ctx

    def post(self, request, ev):
        idtype = request.POST.get('type', None)
        type = get_object_or_404(InvitationType, id=idtype)
        amount = request.POST.get('amount', '0')
        amount = int(amount)
        ispass = request.POST.get('pass', False)

        for x in range(amount):
            invi = Invitation(session=type.session, type=type)
            invi.is_pass = ispass
            invi.gen_order()
            invi.save()
            invi.save_extra_sessions()
            invi.save()

        url = reverse('admin:tickets_invitation_changelist')
        if ispass:
            url += '?is_pass__exact=1'
        return HttpResponseRedirect(url)

gen_invitations = GenInvitationsView.as_view()
