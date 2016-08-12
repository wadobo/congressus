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
from .utils import gen_csv_from_generators


class GenInvitationsView(UserPassesTestMixin, TemplateView):
    template_name = 'invs/generator.html'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated() and u.is_superuser

    def get_context_data(self, *args, **kwargs):
        ctx = super(GenInvitationsView, self).get_context_data(*args, **kwargs)
        ev = get_object_or_404(Event, slug=self.kwargs['ev'])
        ctx['ev'] = ev
        ctx['invs'] = InvitationType.objects.filter(is_pass=False, event=ev)
        ctx['passes'] = InvitationType.objects.filter(is_pass=True, event=ev)
        ctx['menuitem'] = 'inv'
        return ctx

    def post(self, request, ev):
        ids = [(i[len('number_'):], request.POST[i]) for i in request.POST if i.startswith('number_')]

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
            ig.save()
            igs.append(ig)

        # TODO add output type selector:
        #   * csv
        #   * A4
        #   * Thermal

        response = HttpResponse(content_type='application/csv')
        response['Content-Disposition'] = 'filename="invs.csv"'
        response.write(gen_csv_from_generators(igs))
        return response

gen_invitations = GenInvitationsView.as_view()
