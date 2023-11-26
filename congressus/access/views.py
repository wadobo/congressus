from datetime import datetime
from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils import formats
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse

from access.enums import AccessPriority
from access.models import AccessControl
from events.models import Event
from events.models import Session
from events.models import Gate
from tickets.entities import AccessData
from tickets.models import Ticket, MultiPurchase
from invs.models import Invitation

from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


def short_date(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return formats.date_format(dt, "SHORT_DATETIME_FORMAT")


def make_aware(dt):
    if not timezone.is_aware(dt):
        dt = timezone.make_aware(dt)
    return dt


class AccessLogin(TemplateView):
    template_name = "access/login.html"

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get("ev")
        ac = self.kwargs.get("ac")
        ac = get_object_or_404(
            AccessControl.read_objects.all().with_event().with_gates(),
            event__slug=ev,
            slug=ac,
        )
        sessions = Session.objects.filter(space__event=ac.event).with_space()
        ctx = super().get_context_data(*args, **kwargs)
        ctx["ev"] = ac.event
        ctx["ac"] = ac
        ctx["sessions"] = sessions
        ctx["gates"] = ac.event.gates.all()
        return ctx

    def post(self, request, ev=None, ac=None):
        ac = get_object_or_404(AccessControl, event__slug=ev, slug=ac)
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)

        if user is not None:
            have_access = user.groups.filter(name="access").count()
            if user.is_active and have_access:
                # sessions
                sessions_data = request.POST.getlist("sessions", [])
                sessions = Session.objects.filter(
                    space__event__slug=ev, id__in=sessions_data
                )
                request.session["sessions"] = [session.id for session in sessions]

                # gate
                gate = request.POST.get("gate", "")
                if gate:
                    gate = get_object_or_404(Gate, event__slug=ev, id=gate)
                    request.session["gate"] = gate.name
                else:
                    request.session["gate"] = ""
                login(request, user)
                return redirect("access", ev=ac.event.slug, ac=ac.slug)
            else:
                messages.error(
                    request, _("This user can't access in this access control")
                )
        else:
            messages.error(request, _("Invalid username or password"))

        return render(
            request, self.template_name, self.get_context_data(ev=ev, ac=ac.slug)
        )


access_login = AccessLogin.as_view()


class AccessView(UserPassesTestMixin, TemplateView):
    template_name = "access/access.html"

    def get_ac(self):
        ev = self.kwargs["ev"]
        ac = self.kwargs["ac"]
        ac = get_object_or_404(
            AccessControl.objects.all().with_event(),
            event__slug=ev,
            slug=ac,
        )
        return ac

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        return (
            user.groups.filter(name="access").exists()
            and "sessions" in self.request.session
            and "gate" in self.request.session
        )

    def get_login_url(self):
        return reverse("access_login", kwargs=self.kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ac = self.get_ac()
        ctx["ac"] = ac
        sessions = Session.objects.filter(
            id__in=self.request.session.get("sessions", [])
        ).with_space()
        ctx["sessions"] = sessions
        ctx["ws_server"] = settings.WS_SERVER
        ctx["gate"] = self.request.session.get("gate", "")
        return ctx

    def is_inv(self, order):
        return order.startswith(Invitation.prefix())

    def is_multipurchase(self, order):
        return order.startswith(MultiPurchase.prefix())

    def response_json(self, msg, msg2="", st="right"):
        data = {}
        data["st"] = st
        data["extra"] = msg
        data["extra2"] = msg2
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        self.access_control = self.get_ac()
        order = request.POST.get("order", "")
        order = order.strip()
        if len(order) != settings.ORDER_SIZE:
            msg = _("Incorrect readind")
            return self.response_json(msg, st="wrong")

        sessions = self.request.session.get("sessions", [])
        gate = self.request.session.get("gate", "")
        self.sessions_obj = Session.objects.filter(id__in=sessions).get_sessions_dict()

        if self.is_inv(order):
            if not self.access_control.read_inv:
                return self.response_json(_("Can't read invitations"), st="wrong")

            baseticket = (
                Invitation.read_objects.filter(order=order).with_sessions().get()
            )
        elif self.is_multipurchase(order):
            if not self.access_control.read_mp:
                return self.response_json(_("Can't read multipurchase"), st="wrong")

            baseticket = (
                MultiPurchase.objects.filter(order=order, confirmed=True)
                .with_tickets()
                .get()
            )
        else:
            if not self.access_control.read_tickets:
                return self.response_json(_("Can't read individual tickets"), st="wrong")

            baseticket = (
                Ticket.objects.filter(order=order, confirmed=True)
                .with_templates()
                .get()
            )

        if not baseticket:
            return self.response_json(_("Not exists"), st="wrong")

        best = AccessData("wrong", AccessPriority.UNKNOWN, session_id=-1)
        for session_id in sessions:
            access_data = baseticket.can_access(session_id, gate)
            if access_data < best:
                best = access_data

            if access_data.is_best():
                break

        best.set_session(self.sessions_obj)

        if self.get_ac().mark_used:
            baseticket.mark_as_used(best.session_id, best.priority)

        return self.response_json(**best.get_response_data())


access = csrf_exempt(AccessView.as_view())


class AccessLogout(View):
    def get(self, request, ev, ac):
        auth_logout(request)
        return redirect("access", ev=ev, ac=ac)


access_logout = AccessLogout.as_view()


class AccessList(UserPassesTestMixin, TemplateView):
    template_name = "access/list.html"

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.is_superuser

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get("ev")
        ev = get_object_or_404(Event, slug=ev)
        ctx = super(AccessList, self).get_context_data(*args, **kwargs)
        ctx["access"] = ev.access.all()
        ctx["ev"] = ev

        ctx["date"] = timezone.now()

        d = self.request.GET.get("date", "")
        if d:
            date = datetime(*map(int, d.split("-")))
            ctx["date"] = date

        q = Session.objects.extra({"start_date": "date(start)"}).filter(space__event=ev)
        days = q.values_list("start_date", flat=True).distinct().order_by("start_date")
        ctx["days"] = days
        ctx["today"] = timezone.now()
        ctx["menuitem"] = "access"

        return ctx


access_list = AccessList.as_view()
