from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from events.models import Event

from .models import Invitation
from .models import InvitationType
from .models import InvitationGenerator
from .utils import get_ticket_format


class GenInvitationsView(UserPassesTestMixin, TemplateView):
    template_name = 'invs/generator.html'
    DEFAULT_PF = 'csv'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated() and u.is_superuser

    def get_discounts(self):
        ev = self.kwargs['ev']
        ev = get_object_or_404(Event, slug=ev)
        return ev.discounts.all()

    def get_context_data(self, *args, **kwargs):
        ctx = super(GenInvitationsView, self).get_context_data(*args, **kwargs)
        ev = get_object_or_404(Event, slug=self.kwargs['ev'])
        ctx['ev'] = ev
        ctx['invs'] = InvitationType.objects.filter(is_pass=False, event=ev)
        ctx['passes'] = InvitationType.objects.filter(is_pass=True, event=ev)
        ctx['menuitem'] = 'inv'
        ctx['print_formats'] = settings.PRINT_FORMATS
        ctx['default_pf'] = self.DEFAULT_PF
        ctx['discounts'] = self.get_discounts()
        return ctx

    def post(self, request, ev):
        ids = [(i[len('number_'):], request.POST[i]) for i in request.POST if i.startswith('number_')]
        print_format = request.POST.get('print-format', self.DEFAULT_PF)
        seats = request.POST.get('seats', '')

        igs = []
        for i, v in ids:
            itype = InvitationType.objects.get(pk=i)
            amount = int(v)

            if not amount:
                continue

            price = request.POST.get('price', '0')
            comment = request.POST.get('comment', '')

            ig = InvitationGenerator(type=itype, amount=amount,
                                     price=price, concept=comment)
            if seats:
                ig.seats = seats
            ig.clean()
            ig.save()
            igs.append(ig)

        response = get_ticket_format(igs, pf=print_format)
        return response

gen_invitations = GenInvitationsView.as_view()
