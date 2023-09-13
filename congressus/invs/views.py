from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.http.response import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect

from events.models import Event
from invs.models import InvitationType, InvitationGenerator


class GenInvitationsView(UserPassesTestMixin, TemplateView):
    template_name = "invs/generator.html"
    PRINT_FORMATS = ["CSV", "HTML", "PDF"]

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.is_superuser

    def get_discounts(self):
        ev = self.kwargs["ev"]
        ev = get_object_or_404(Event, slug=ev)
        return ev.discounts.all()

    def get_context_data(self, *args, **kwargs):
        ctx = super(GenInvitationsView, self).get_context_data(*args, **kwargs)
        ev = get_object_or_404(Event, slug=self.kwargs["ev"])
        ctx["ev"] = ev
        ctx["invs"] = InvitationType.objects.filter(is_pass=False, event=ev)
        ctx["passes"] = InvitationType.objects.filter(is_pass=True, event=ev)
        ctx["menuitem"] = "inv"
        ctx["print_formats"] = self.PRINT_FORMATS
        ctx["discounts"] = self.get_discounts()
        return ctx

    def post(self, request, ev):
        ids = [
            (i[len("number_"):], request.POST[i])
            for i in request.POST
            if i.startswith("number_") and request.POST[i] != "0"
        ]
        if len(ids) != 1:
            messages.error(request, _("Please select onlye one invitation or pass"))
            return redirect(request.path)

        print_format = request.POST.get("print-format", self.PRINT_FORMATS[0])
        seats = request.POST.get("seats", "")
        price = float(request.POST.get("price", "0"))
        comment = request.POST.get("comment", "")

        inv_type_id = int(ids[0][0])
        amount = int(ids[0][1])
        if not amount:
            messages.error(request, _("Invalid amount"))
            return redirect(request.path)

        generator = InvitationGenerator(
            type_id=inv_type_id,
            amount=amount,
            price=price,
            concept=comment,
            seats=seats,
        )

        try:
            generator.clean()
        except ValidationError as err:
            messages.error(request, err.message)
            return redirect(request.path)

        generator.save()

        return generator.get_from_print_format(print_format)


gen_invitations = GenInvitationsView.as_view()
