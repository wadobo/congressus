from datetime import datetime
from typing import TYPE_CHECKING

from django.db import models
from django.db.models.signals import post_delete
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.response import HttpResponse
from django.template import Context, Template, loader
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML

from access.enums import AccessPriority
from events.models import Event
from events.models import Session
from events.models import Gate
from events.models import SeatLayout
from invs.managers import ReadInvitationManager, WriteInvitationManager
from tickets.entities import AccessData
from tickets.models import BaseExtraData, BaseTicketModel, TicketSeatHold
from tickets.utils import get_seats_by_str


if TYPE_CHECKING:
    from events.models import TicketTemplate


def short_hour(date_time):
    if timezone.is_aware(date_time):
        date_time = timezone.localtime(date_time)
    return formats.date_format(date_time, "H:i")


def assert_if_not_prefetch_usedin(func):
    def wrapper(self, *args, **kwargs):
        if (
            not hasattr(self, "_prefetched_objects_cache")
            or "usedin" not in self._prefetched_objects_cache
        ):
            raise AssertionError(
                "Invalid use of invitation, you need load InvUsedInSession with "
                "prefetch_related('usedin')"
            )
        return func(self, *args, **kwargs)

    return wrapper


class InvitationType(models.Model):
    name = models.CharField(_("name"), max_length=200)
    is_pass = models.BooleanField(_("is pass"), default=False)
    one_time_for_session = models.BooleanField(
        _("one time for session"),
        default=False,
        help_text=_(
            "This is used for passes that will be "
            "only valid one time for each session. "
            "Invitations always have only one use. "
            "So this is ignored in invitations."
        ),
    )

    event = models.ForeignKey(
        Event,
        related_name="invitation_types",
        verbose_name=_("event"),
        on_delete=models.CASCADE,
    )
    sessions = models.ManyToManyField(
        Session, related_name="invitation_types", blank=True, verbose_name=_("sessions")
    )

    gates = models.ManyToManyField(Gate, blank=True, verbose_name=_("gates"))
    start = models.DateTimeField(_("start date"), null=True, blank=True)
    end = models.DateTimeField(_("end date"), null=True, blank=True)
    template = models.ForeignKey(
        "events.TicketTemplate", verbose_name=_("template"), on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("invitation type")
        verbose_name_plural = _("invitation types")
        ordering = ("-event__name", "name")

    def __str__(self):
        return self.name


class Invitation(models.Model, BaseTicketModel, BaseExtraData):
    type = models.ForeignKey(
        InvitationType,
        related_name="invitations",
        verbose_name=_("invitation type"),
        on_delete=models.CASCADE,
    )

    generator = models.ForeignKey(
        "InvitationGenerator",
        related_name="invitations",
        null=True,
        blank=True,
        verbose_name=_("generator"),
        on_delete=models.CASCADE,
    )

    order = models.CharField(_("order"), max_length=200, unique=True)
    created = models.DateTimeField(_("created at"), auto_now_add=True)
    extra_data = models.TextField(_("extra data"), blank=True, null=True)
    is_pass = models.BooleanField(_("is pass"), default=False)

    # row-col
    seat_layout = models.ForeignKey(
        SeatLayout,
        null=True,
        blank=True,
        verbose_name=_("seat layout"),
        on_delete=models.CASCADE,
    )
    seat = models.CharField(_("seat"), max_length=20, null=True, blank=True)
    name = models.CharField(_("name"), max_length=200, null=True, blank=True)

    objects = WriteInvitationManager()
    read_objects = ReadInvitationManager()

    class Meta:
        verbose_name = _("invitation")
        verbose_name_plural = _("invitations")

    @classmethod
    def prefix(cls) -> str:
        return "I"

    @property
    def used(self):
        return self.usedin.exists()

    @property
    def used_date(self):
        try:
            return self.usedin.all()[0].date
        except Exception:
            return None

    @property
    def extra_used(self):
        extra_sessions = self.get_extra_data("extra_sessions")
        if extra_sessions is None:
            return False

        sessions_used = [
            session.get("session", None)
            for session in extra_sessions
            if session.get("used") is True
        ]
        if sessions_used:
            return sessions_used[0]

        return False

    @property
    def extra_used_date(self):
        extra_sessions = self.get_extra_data("extra_sessions")
        if extra_sessions is None:
            return None

        sessions_used_date = [
            session.get("used_date", None)
            for session in extra_sessions
            if session.get("used") is True
        ]
        if sessions_used_date:
            return sessions_used_date[0]

        return None

    @property
    def wcode(self) -> str:
        if self.generator:
            return "GEN" + str(self.generator.id)

        return "INV"

    @property
    def initials(self):
        if self.type.is_pass:
            return "PAS"

        return "INV"

    @property
    def text(self):
        if self.generator:
            return self.generator.concept

        return self.type.name

    @property
    def date(self):
        sstart = self.type.start
        send = self.type.end

        if not sstart or not send:
            return ""

        return _("%(date)s (%(start)s)") % {
            "date": formats.date_format(sstart, "l d/m/Y"),
            "start": short_hour(sstart),
        }

    @property
    def total_price(self) -> str:
        if self.sold_in_window:
            price = self.get_window_price()
        else:
            price = self.get_price()

        if not price:
            return ""

        price = _("%4.2f €") % price
        tax = self.get_tax()

        taxtext = _("TAX INC.")
        return (
            f'<font class="price">{price}</font>   '
            f'<font class="tax">{tax}% {taxtext}</font>'
        )

    def get_template(self) -> "TicketTemplate":
        return self.type.template

    def html_format(self):
        ticket_template = self.get_template()
        tpl_child = Template(ticket_template.extra_html)
        qr = self.gen_qr()
        ctx = Context(
            {"ticket": self, "template": ticket_template, "qr": qr, "qr_group": qr}
        )
        preview_data = tpl_child.render(ctx)

        template = loader.get_template("tickets/preview.html")
        return template.render(
            {
                "template": ticket_template,
                "qr": qr,
                "qr_group": qr,
                "preview": preview_data,
            }
        )

    def get_html(self):
        return HttpResponse(self.html_format())

    def pdf_format(self, request=None):
        html = self.html_format()
        kwargs = {"string": html}
        if request:
            kwargs["base_url"] = request.build_absolute_uri()
        else:
            kwargs["base_url"] = settings.FULL_DOMAIN
        return HTML(**kwargs).write_pdf()

    def get_pdf(self, request):
        pdf = self.pdf_format(request=request)
        response = HttpResponse(content_type="application/pdf")
        fname = 'attachment; filename="tickets.pdf"'
        response["Content-Disposition"] = fname
        response.write(pdf)
        return response

    def event(self):
        return self.type.event

    @assert_if_not_prefetch_usedin
    def is_used(self, session_id):
        return session_id in [session.session.id for session in self.usedin.all()]

    @assert_if_not_prefetch_usedin
    def get_used_date(self, session_id):
        used_date = None
        for session in self.usedin.all():
            if session.session.id == session_id:
                used_date = session.date
                break

        return used_date

    def set_used(self, session_id):
        i, created = InvUsedInSession.objects.get_or_create(
            session_id=session_id, inv=self
        )
        i.save()

    def get_gate_name(self):
        return ", ".join(i.name for i in self.type.gates.all())

    def save_extra_sessions(self):
        data = []
        for session in self.type.sessions.all():
            for extra in session.orig_sessions.all():
                prev = self.get_extra_session(extra.extra.id)
                data.append(
                    {
                        "session": extra.extra.id,
                        "start": timezone.make_naive(extra.start).strftime(
                            settings.DATETIME_FORMAT
                        ),
                        "end": timezone.make_naive(extra.end).strftime(
                            settings.DATETIME_FORMAT
                        ),
                        "used": prev["used"] if prev else extra.used,
                    }
                )
        self.set_extra_data("extra_sessions", data)

    @property
    def sold_in_window(self):
        return False

    def get_price(self):
        if self.generator:
            return self.generator.price

        return 0

    def get_tax(self):
        if self.generator:
            return self.generator.tax
        return 0

    def cseat(self):
        if not self.seat:
            return None
        row, column = self.seat.split("-")
        return _("L%(layout)s-R%(row)s-C%(col)s") % {
            "layout": self.seat_layout.name,
            "row": row,
            "col": column,
        }

    cseat.short_description = _("seat")

    def seat_row(self):
        if not self.seat:
            return None
        row, column = self.seat.split("-")
        return row

    def seat_column(self):
        if not self.seat:
            return None
        row, column = self.seat.split("-")
        return column

    def remove_hold_seats(self):
        if self.seat_layout and self.seat:
            for s in self.type.sessions.all():
                tsh = TicketSeatHold.objects.filter(
                    session=s, layout=self.seat_layout, type="R", seat=self.seat
                )
                if tsh:
                    tsh.delete()

    def can_access_extra(self, session_id, gate_name) -> AccessData:
        from access.views import make_aware

        extra = self.get_extra_session(session_id)
        if not extra:
            return AccessData(
                st="wrong",
                priority=AccessPriority.INVALID_SESSION,
                session_id=session_id,
            )

        if extra.get("used"):
            return AccessData(
                st="wrong",
                priority=AccessPriority.USED,
                session_id=session_id,
                date=datetime.strptime(extra["used_date"], settings.DATETIME_FORMAT),
            )

        end = datetime.strptime(extra["end"], settings.DATETIME_FORMAT)
        if make_aware(end) < timezone.now():
            return AccessData(
                st="wrong",
                priority=AccessPriority.HOUR_EXPIRED,
                session_id=session_id,
                date=end,
            )

        start = datetime.strptime(extra["start"], settings.DATETIME_FORMAT)
        if make_aware(start) > timezone.now():
            return AccessData(
                st="wrong",
                priority=AccessPriority.HOUR_TOO_SOON,
                session_id=session_id,
                date=start,
            )

        return AccessData(
            st="right", priority=AccessPriority.VALID_EXTRA, session_id=session_id
        )

    def can_access(self, session_id, gate_name) -> AccessData:
        if self.is_pass and self.is_used(session_id):
            return AccessData(
                st="wrong",
                priority=AccessPriority.USED,
                session_id=session_id,
                date=self.get_used_date(session_id),
            )

        if not self.is_pass and self.used:
            return AccessData(
                st="wrong",
                priority=AccessPriority.USED,
                session_id=session_id,
                date=self.used_date,
            )

        if not self.is_pass and self.extra_used:
            extra_used_date = datetime.strptime(
                self.extra_used_date, settings.DATETIME_FORMAT
            )
            if extra_used_date.date() != datetime.now().date():
                # TODO: comprobar que la sesión extra usada es una sesión extra de la sesión
                # actual, sino devolver usado. Ahora está por fecha y es funcional
                return AccessData(
                    st="wrong",
                    priority=AccessPriority.USED,
                    session_id=session_id,
                    date=extra_used_date,
                )

        extra_access_data = self.can_access_extra(session_id, gate_name)
        if not extra_access_data.is_valid() and session_id not in [
            session.id for session in self.type.sessions.all()
        ]:
            priority = AccessPriority.INVALID_SESSION

            if extra_access_data.priority < priority:
                return extra_access_data

            return AccessData(
                st="wrong",
                priority=priority,
                session_id=session_id,
            )

        if extra_access_data.is_valid():
            return extra_access_data

        if settings.ACCESS_VALIDATE_INV_HOURS:
            now = timezone.now()
            if self.type.end and now > self.type.end:
                priority = AccessPriority.HOUR_EXPIRED

                if extra_access_data.priority < priority:
                    return extra_access_data

                return AccessData(
                    st="wrong",
                    priority=priority,
                    session_id=session_id,
                    date=self.type.end,
                )

            if self.type.start and now < self.type.start:
                priority = AccessPriority.HOUR_TOO_SOON

                if extra_access_data.priority < priority:
                    return extra_access_data

                return AccessData(
                    st="wrong",
                    priority=priority,
                    session_id=session_id,
                    date=self.type.start,
                )

        if gate_name and gate_name not in [gate.name for gate in self.type.gates.all()]:
            priority = AccessPriority.INVALID_GATE

            if extra_access_data.priority < priority:
                return extra_access_data

            return AccessData(
                st="maybe",
                priority=AccessPriority.INVALID_GATE,
                session_id=session_id,
                gate_name=gate_name,
            )

        return AccessData(
            st="right", priority=AccessPriority.VALID_NORMAL, session_id=session_id
        )

    def mark_as_used(self, session_id, priority):
        if self.is_pass and not self.type.one_time_for_session:
            return

        if priority == AccessPriority.VALID_NORMAL:
            self.set_used(session_id)
        elif priority == AccessPriority.VALID_EXTRA:
            self.set_extra_session_to_used(session_id)
            self.save()

    def __str__(self):
        return self.order


class InvUsedInSession(models.Model):
    inv = models.ForeignKey(
        Invitation,
        related_name="usedin",
        verbose_name=_("invitation"),
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
        related_name="usedby",
        verbose_name=_("session"),
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("invitation used in")
        verbose_name_plural = _("invitations used in")


class InvitationGenerator(models.Model):
    type = models.ForeignKey(
        InvitationType, verbose_name=_("type"), on_delete=models.CASCADE
    )
    amount = models.IntegerField(_("amount"), default=1)
    price = models.IntegerField(_("price"), blank=True, null=True)
    tax = models.IntegerField(_("tax"), null=True)
    concept = models.CharField(_("concept"), max_length=200)
    seats = models.CharField(
        _("seats"),
        max_length=1024,
        blank=True,
        null=True,
        help_text="C1[1-1,1-3]; C2[2-1:2-4]",
    )
    created = models.DateTimeField(_("created at"), auto_now_add=True)

    def __str__(self):
        return f"{self.type.name} - {self.amount} - {self.concept}"

    class Meta:
        verbose_name = _("invitation generator")
        verbose_name_plural = _("invitation generators")
        ordering = ("-created",)

    def window_code(self):
        """
        This is a generator code, but use the name window_code to be the same
        of tickets. Example code: INVMMDDHHMM
        """
        prefix = "INV"
        postfix = self.created.strftime("%m%d%H%M")
        return prefix + postfix

    def get_seats(self):
        return get_seats_by_str(self.seats)

    def clean(self):
        super().clean()
        # only validate on creation
        if self.seats and not self.id:
            seats = 0
            for val in self.get_seats().values():
                seats += len(val)
            if seats != self.amount:
                raise ValidationError(_("Seats number should be equal to amount"))

    def save(self, *args, **kwargs):
        should_generate = not self.id
        super().save(*args, **kwargs)
        if should_generate:
            self.generate()

    def get_from_print_format(self, print_format):
        if print_format == "CSV":
            csv = []
            name = self.type.name
            for i, inv in enumerate(self.invitations.all()):
                line = "%s,%s" % (inv.order, name)
                if inv.seat_layout and inv.seat:
                    row, col = inv.seat.split("-")
                    col = int(col) + inv.seat_layout.column_start_number - 1
                    line += ",%s,%s,%s" % (inv.seat_layout.gate, row, col)
                csv.append(line)

            csv_out = []
            for i, line in enumerate(csv):
                csv_out.append(("%d," % (i + 1)) + line)

            response = HttpResponse(content_type="application/csv")
            response["Content-Disposition"] = 'filename="invs.csv"'
            response.write("\n".join(csv_out))
            return response

        if print_format == "HTML":
            return self.get_html()

        if print_format == "PDF":
            return self.get_pdf()

    def html_format(self):
        html = ""
        for inv in self.invitations.select_related(
            "seat_layout", "seat_layout__gate", "generator", "type", "type__template"
        ).all():
            html += inv.html_format()
        return html

    def pdf_format(self, request=None):
        html = self.html_format()
        kwargs = {"string": html}
        if request:
            kwargs["base_url"] = request.build_absolute_uri()
        return HTML(**kwargs).write_pdf()

    def get_html(self):
        return HttpResponse(self.html_format())

    def get_pdf(self):
        response = HttpResponse(content_type="application/pdf")
        fname = 'attachment; filename="tickets.pdf"'
        response["Content-Disposition"] = fname
        response.write(self.pdf_format())
        return response

    def generate(self):
        # SEAT LAYOUTS
        seat_list = []
        if self.seats:
            seats = self.get_seats()
            layouts = SeatLayout.objects.filter(name__in=seats.keys())
            for layout in layouts:
                seat_list += [[layout, value] for value in seats.get(layout.name)]

        # ORDERS
        orders = Invitation.gen_orders(amount=self.amount)
        invalid_orders = Invitation.objects.filter(order__in=orders).values_list(
            "order", flat=True
        )

        # Extra sessions
        data = []
        session_first = self.type.sessions.first()
        for session in self.type.sessions.all():
            for extra in session.orig_sessions.all():
                data.append(
                    {
                        "session": extra.extra.id,
                        "start": timezone.make_naive(extra.start).strftime(
                            settings.DATETIME_FORMAT
                        ),
                        "end": timezone.make_naive(extra.end).strftime(
                            settings.DATETIME_FORMAT
                        ),
                        "used": extra.used,
                    }
                )

        invis = []
        for n in range(self.amount):
            invi = Invitation(type=self.type, generator=self, is_pass=self.type.is_pass)
            if seat_list:
                invi.seat_layout, invi.seat = seat_list[n]

            invi.order = orders[n]
            if invi.order in invalid_orders:
                invi.gen_order()

            invi.set_extra_data("extra_sessions", data)
            invis.append(invi)

            if seat_list:
                tsh, new = TicketSeatHold.objects.get_or_create(
                    session=session_first,
                    layout=invi.seat_layout,
                    seat=invi.seat,
                    defaults={"type": "R", "client": "INV"},
                )
                if not new:
                    tsh.type = "R"
                    tsh.client = "INV"
                    tsh.save()

        Invitation.objects.bulk_create(invis)

    def regenerate(self):
        """This functionality has been created to regenerate extra_sessions when we
        already create invitations and the sessions are incorrect."""

        extra_sessions = []
        for session in self.type.sessions.all():
            for extra in session.orig_sessions.all():
                extra_sessions.append(
                    {
                        "session": extra.extra.id,
                        "start": timezone.make_naive(extra.start).strftime(
                            settings.DATETIME_FORMAT
                        ),
                        "end": timezone.make_naive(extra.end).strftime(
                            settings.DATETIME_FORMAT
                        ),
                        "used": extra.used,
                    }
                )

        all_invis = []
        for invi in self.invitations.all():
            invi.set_extra_data("extra_sessions", extra_sessions)
            invi.is_pass = self.type.is_pass
            invi.type = self.type
            all_invis.append(invi)

        Invitation.objects.bulk_update(all_invis, ["is_pass", "type", "extra_data"])


def remove_seatholds(sender, instance, using, **kwargs):
    instance.remove_hold_seats()


post_delete.connect(remove_seatholds, Invitation)
