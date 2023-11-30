from __future__ import annotations

import base64
import json
import random
import string
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING

import qrcode
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.db.models.signals import post_save
from django.http.response import HttpResponse
from django.template import Context, Template, loader
from django.template.loader import get_template
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from PIL import ImageDraw, ImageFont
from weasyprint import HTML

from access.enums import AccessPriority
from events.choices import SessionTemplate
from events.models import (
    Discount,
    Event,
    InvCode,
    SeatLayout,
    Session,
)
from tickets.entities import AccessData
from tickets.managers import (
    ReadMultiPurchaseManager,
    ReadTicketManager,
    WriteMultiPurchaseManager,
    WriteTicketManager,
)

if TYPE_CHECKING:
    from events.models import TicketTemplate


WARNING_TYPES = (("req", _("Required")),)

SEATHOLD_TYPES = (
    ("H", _("Holded")),
    ("C", _("Confirming")),
    ("P", _("Paying")),
    ("R", _("Reserved")),
)

PAYMENT_TYPES = (
    ("tpv", _("TPV")),
    ("paypal", _("Paypal")),
    ("stripe", _("Stripe")),
    ("twcash", _("Cash, Ticket Window")),
    ("twtpv", _("TPV, Ticket Window")),
)


def short_hour(date_time):
    if timezone.is_aware(date_time):
        date_time = timezone.localtime(date_time)
    return formats.date_format(date_time, "H:i")


def assert_if_not_prefetch_tickets(func):
    def wrapper(self, *args, **kwargs):
        if (
            not hasattr(self, "_prefetched_objects_cache")
            or "tickets" not in self._prefetched_objects_cache
        ):
            raise AssertionError(
                "Invalid use of has_valid_tickets_with_extra_session, you need "
                "load MultiPurchase with prefetch_related('tickets')"
            )
        return func(self, *args, **kwargs)

    return wrapper


class BaseTicketModel:
    @classmethod
    def prefix(cls) -> str:
        raise NotImplementedError

    def gen_order(
        self, *, length: int = settings.ORDER_SIZE, save: bool = True
    ) -> None:
        prefix = self.prefix()
        chars = string.ascii_uppercase + string.digits
        _length = length - len(prefix)
        while 1:
            order = prefix + "".join(random.choice(chars) for _ in range(_length))
            if not self.is_order_used(order):
                break

        self.order = order
        if save:
            self.save()

    @classmethod
    def gen_orders(cls, *, length: int = settings.ORDER_SIZE, amount: int = 1) -> None:
        prefix = cls.prefix()
        chars = string.ascii_uppercase + string.digits
        _length = length - len(prefix)

        chars = string.ascii_uppercase + string.digits
        orders = set()
        while len(orders) < amount:
            orders.add(prefix + "".join(random.choice(chars) for _ in range(_length)))
        return tuple(orders)

    def is_order_used(self, order):
        return self.__class__.objects.filter(order=order).exists()

    def gen_qr(self, qr_size: float = 10, border: int = 4, number: int = 0):
        stream = BytesIO()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=qr_size + 2 * border,
            border=border,
        )
        qr.add_data(self.order)
        qr.make(fit=True)

        qr_img = qr.make_image()

        if number:
            draw = ImageDraw.Draw(qr_img)
            circle_size = qr_img.pixel_size / 4
            draw.ellipse(
                (
                    int((qr_img.size[0] - circle_size) / 2),
                    int((qr_img.size[1] - circle_size) / 2),
                    int((qr_img.size[0] + circle_size) / 2),
                    int((qr_img.size[1] + circle_size) / 2),
                ),
                fill="white",
                outline="black",
                width=4,
            )

            font = ImageFont.truetype("static/fonts/Aileron-Bold.otf", size=96)
            draw.text(
                xy=(int(qr_img.size[0] / 2), int(qr_img.size[1] / 2)),
                text=str(number),
                anchor="mm",
                font=font,
            )

        qr_img.save(stream, format="png")
        return base64.b64encode(stream.getvalue()).decode("utf8")

    def can_access(self, session_id, gate_name) -> AccessData:
        raise NotImplementedError

    def mark_as_used(self, session_id, priority):
        raise NotImplementedError


class BaseTicketMixing:
    """
    Common base class for ticket and MultiPurchase to avoid django model
    inheritance, but to use the same code for methods
    """

    def space(self):
        return self.session.space

    def event(self):
        return self.space().event

    def gen_order_tpv(self):
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.order_tpv = timezone.now().strftime("%y%m%d")
        self.order_tpv += "".join(random.choice(chars) for _ in range(6))
        self.save()

    def get_price(self, mp=None):
        total = self.session.price
        if mp is None:
            mp = self.mp
        if mp and mp.discount and mp.discount.unit:
            total = mp.discount.apply_to(total)
        return total

    def get_tax(self):
        return self.session.tax

    def get_window_price(self, window=None, mp=None):
        if not window:
            window = self.mp.sales.all()[0].window
        total = window.get_price(self.session)

        if mp is None:
            mp = self.mp
        if mp and mp.discount and mp.discount.unit:
            total = mp.discount.apply_to(total)
        return total

    def send_reg_email(self):
        tmpl = get_template("emails/reg.txt")
        body = tmpl.render({"ticket": self})
        email = EmailMessage(
            _("New Register / %s") % self.event(),
            body,
            settings.FROM_EMAIL,
            [self.event().admin],
            reply_to=[self.email],
        )
        email.send(fail_silently=False)

    def send_confirm_email(self):
        self.confirm_sent = True
        self.save()

        if self.email == settings.FROM_EMAIL:
            # ticket from ticket window
            return

        # email to admin
        tmpl = get_template("emails/confirm.txt")
        body = tmpl.render({"ticket": self})
        email = EmailMessage(
            _("Confirmed / %s") % self.event(),
            body,
            settings.FROM_EMAIL,
            [self.event().admin],
            reply_to=[self.email],
        )
        email.send(fail_silently=False)

        # email to user
        e = self.event().get_email()

        extra = {}
        if self.extra_data:
            extra = json.loads(self.extra_data)

        if e:
            subject = Template(e.subject).render(
                Context({"ticket": self, "extra": extra})
            )
            body = Template(e.body).render(Context({"ticket": self, "extra": extra}))
        else:
            tmpl = get_template("emails/subject-confirm-user.txt")
            subject = tmpl.render({"ticket": self, "extra": extra})
            tmpl = get_template("emails/confirm-user.txt")
            body = tmpl.render({"ticket": self, "extra": extra})

        body = body.replace("TICKETID", self.order)

        email = EmailMessage(subject.strip(), body, settings.FROM_EMAIL, [self.email])

        if e:
            # adding attachments
            for att in e.attachs.all():
                email.attach_file(att.attach.path)

        filename = "ticket_%s.pdf" % self.order
        email.attach(
            filename,
            self.pdf_format(session_template=SessionTemplate.ONLINE),
            "application/pdf",
        )
        email.send(fail_silently=False)

    def get_absolute_url(self):
        url = "payment" if not self.confirmed else "thanks"

        order = self.order
        if hasattr(self, "mp") and self.mp:
            order = self.mp.order

        return reverse(url, kwargs={"order": order})

    def is_mp(self):
        return False

    def hold_seats(self):
        all_tk = []
        if self.is_mp():
            all_tk = self.tickets.only("session", "seat_layout", "seat").filter(
                session__space__numbered=True
            )
        elif self.session.space.numbered:
            all_tk = [self]

        # Save reserved ticket in SeatHold
        for t in all_tk:
            tsh, created = TicketSeatHold.objects.get_or_create(
                session=t.session, layout=t.seat_layout, seat=t.seat, type="R"
            )
            tsh.client = "CONFIRMED"
            tsh.save()

            # removing hold seats not confirmed
            TicketSeatHold.objects.filter(
                session=t.session,
                layout=t.seat_layout,
                seat=t.seat,
                type__in=["H", "C", "P"],
            ).delete()

    def remove_hold_seats(self):
        all_tk: list[Ticket] = []
        if self.is_mp():
            all_tk = self.tickets.filter(session__space__numbered=True)
        elif self.session.space.numbered:
            all_tk = [self]

        # Save reserved ticket in SeatHold
        for t in all_tk:
            TicketSeatHold.objects.filter(
                session=t.session, layout=t.seat_layout, type="R", seat=t.seat
            ).delete()

    def confirm(self, method="tpv"):
        self.confirmed = True
        self.payment_method = method

        if self.is_mp():
            self.tickets.update(payment_method=method)

        self.hold_seats()
        self.save()

    def set_error(self, error, info):
        self.tpv_error = error
        self.tpv_error_info = info
        self.save()

    def get_html(self, session_template: SessionTemplate, preview_pdf: bool = False):
        return HttpResponse(
            self.html_format(session_template=session_template, preview_pdf=preview_pdf)
        )

    def get_pdf(self, session_template: SessionTemplate, request):
        pdf = self.pdf_format(session_template=session_template, request=request)
        response = HttpResponse(content_type="application/pdf")
        fname = 'attachment; filename="tickets.pdf"'
        response["Content-Disposition"] = fname
        response.write(pdf)
        return response

    def pdf_format(self, session_template: SessionTemplate, request=None):
        html = self.html_format(session_template=session_template)
        kwargs = {"string": html}
        if request:
            kwargs["base_url"] = request.build_absolute_uri()
        else:
            kwargs["base_url"] = settings.FULL_DOMAIN
        return HTML(**kwargs).write_pdf()


class BaseExtraData:
    def seatinfo(self):
        seatinfo = ""
        if self.seat:
            seatinfo += _("SECTOR") + ": " + self.seat_layout.name
            seatinfo += _("ROW") + ": " + self.seat_row()
            seatinfo += _("SEAT") + ": " + self.seat_column()
        return seatinfo

    def get_extra_data(self, key):
        data = {}
        if not self.extra_data:
            return None
        else:
            data = json.loads(self.extra_data)
        return data.get(key, None)

    def set_extra_data(self, key, value):
        data = json.loads(self.extra_data or "{}")
        data[key] = value
        self.extra_data = json.dumps(data)

    def get_extras_dict(self):
        extras = {}
        # excluding html, we don't want to show in visualization
        for field in self.event().fields.exclude(type="html"):
            extras[field.label] = self.get_extra_data(field.label)
        return extras

    def get_extras(self):
        extras = []
        # excluding html, we don't want to show in visualization
        for field in self.event().fields.exclude(type="html"):
            extras.append({"field": field, "value": self.get_extra_data(field.label)})
        return extras

    def get_extra_sessions(self):
        return self.get_extra_data("extra_sessions") or []

    def get_extra_session(self, pk):
        for extra in self.get_extra_sessions():
            if extra["session"] == pk:
                return extra
        return None

    def set_extra_session_to_used(self, pk):
        data = self.get_extra_sessions()
        for extra in data:
            if extra.get("session") == pk:
                extra["used"] = True
                dt = timezone.localtime(timezone.now())
                extra["used_date"] = dt.strftime(settings.DATETIME_FORMAT)
                break
        self.set_extra_data("extra_sessions", data)

    def save_extra_sessions(self):
        data = []
        for extra in self.session.orig_sessions.all():
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


class MultiPurchase(models.Model, BaseTicketModel, BaseTicketMixing, BaseExtraData):
    ev = models.ForeignKey(
        Event, related_name="mps", verbose_name=_("event"), on_delete=models.CASCADE
    )

    order = models.CharField(_("order"), max_length=200, unique=True)
    order_tpv = models.CharField(_("order TPV"), max_length=12, blank=True, null=True)

    tpv_error = models.CharField(_("error TPV"), max_length=200, blank=True, null=True)
    tpv_error_info = models.CharField(
        _("error TPV info"), max_length=200, blank=True, null=True
    )

    payment_method = models.CharField(
        _("payment method"), max_length=10, choices=PAYMENT_TYPES, blank=True, null=True
    )

    created = models.DateTimeField(_("created at"), auto_now_add=True)
    confirmed_date = models.DateTimeField(_("confirmed at"), blank=True, null=True)
    confirmed = models.BooleanField(_("confirmed"), default=False)
    confirm_sent = models.BooleanField(_("confirmation sent"), default=False)
    discount = models.ForeignKey(
        Discount,
        related_name="mps",
        verbose_name=_("discount"),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    # Form Fields
    email = models.EmailField(_("email"))

    extra_data = models.TextField(_("extra data"), blank=True, null=True)

    read_objects = ReadMultiPurchaseManager()
    objects = WriteMultiPurchaseManager()

    def save(self, *args, **kw):
        if self.pk is not None:
            orig = MultiPurchase.objects.get(pk=self.pk)
            confirm = self.confirmed != orig.confirmed
        else:
            confirm = True

        if self.pk and confirm:
            for t in self.tickets.all():
                t.confirmed = self.confirmed
                t.save()
            if self.confirmed:
                self.confirmed_date = timezone.now()

        super().save(*args, **kw)

    @classmethod
    def prefix(cls) -> str:
        return "M"

    @property
    def price(self):
        total = sum([i.get_price(mp=self) for i in self.tickets.all()])
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    @property
    def real_price(self):
        tickets = self.tickets.all()
        if not len(tickets):
            return 0

        if tickets[0].sold_in_window:
            sale = self.sales.all()[0]
            total = sum(
                i.get_window_price(window=sale.window, mp=self) for i in tickets
            )
        else:
            total = sum(i.get_price(mp=self) for i in tickets)
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    @property
    def num_tickets(self) -> int:
        return len(self.tickets.all())

    @property
    def ticket_window_code(self) -> str:
        tws = [sale.window.code for sale in self.sales.all()]
        if not tws:
            return "-"
        return tws[0]

    def space(self):
        """Multiple spaces"""
        return None

    def event(self):
        return self.ev

    def get_price(self):
        total = sum(i.get_price(mp=self) for i in self.all_tickets())
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    def get_window_price(self):
        total = sum(i.get_window_price() for i in self.all_tickets())
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    def get_real_price(self):
        all_tickets = self.all_tickets()
        if not len(all_tickets):
            return 0

        if all_tickets[0].sold_in_window:
            total = sum(i.get_window_price() for i in all_tickets)
        else:
            total = sum(i.get_price(mp=self) for i in all_tickets)
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    def is_mp(self):
        return True

    def html_format(self, session_template: SessionTemplate, preview_pdf: bool = False):
        html = ""
        tickets = self.tickets.all().order_by("session_id")
        has_conflict = tickets.has_session_conflict()

        ticket_group_by_session = tickets.group_by_sessions()
        for session_id, tickets in ticket_group_by_session.items():
            qr_group = None
            if not has_conflict and (1 < len(tickets) <= 20):
                qr_group = self.gen_qr(number=len(tickets))

            for ticket in tickets:
                html += ticket.html_format(
                    session_template=session_template,
                    preview_pdf=preview_pdf,
                    qr_group=qr_group,
                )
        return html

    def all_tickets(self):
        return self.tickets.select_related("session", "session__template").order_by(
            "session__start"
        )

    def delete(self, *args, **kwargs):
        self.remove_hold_seats()
        super(MultiPurchase, self).delete(*args, **kwargs)

    def window_code(self):
        """
        ONLMMDDHHMM
        """

        prefix = "ONL"
        postfix = timezone.localtime(self.created).strftime("%m%d%H%M")

        self.sales.values_list("window__code", flat=True)

        return prefix + postfix

    @property
    def wcode(self) -> str:
        return self.window_code()

    @property
    def initials(self):
        space = self.session.space.name
        session = self.session.name

        if self.session.short_name:
            return self.session.short_name
        return _("T") + space[0].upper() + session[0].upper()

    @property
    def text(self):
        data = {
            "space": self.session.space.name.capitalize(),
            "session": self.session.name.capitalize(),
        }
        return _("Ticket %(space)s %(session)s") % data

    @property
    def date(self):
        sstart = self.session.start
        send = self.session.end

        start = formats.date_format(sstart, "l d/m/Y")

        dateformats = {
            "start": _("%(date)s (%(start)s)"),
            "complete": _("%(date)s (%(start)s to %(end)s)"),
            "onlydate": _("%(date)s"),
        }
        strdate = dateformats[self.session.dateformat]

        return strdate % {
            "date": start,
            "start": short_hour(sstart),
            "end": short_hour(send),
        }

    # @property
    # def order(self):
    #    if self.mp:
    #        return self.mp.order_tpv or ''
    #    return ''

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

    def get_extra_session(self, pk):
        for extra in self.get_extra_sessions():
            if extra["session"] == pk:
                return extra
        return None

    def can_access(self, session_id, gate_name) -> AccessData:
        best_access = AccessData("wrong", AccessPriority.UNKNOWN, session_id=-1)

        group_tickets = self.tickets_group_by_sessions()
        for group_session_id, tickets in group_tickets.items():
            access_datas = [
                ticket.can_access(session_id, gate_name) for ticket in tickets
            ]
            if len(access_datas) == 1:
                if access_datas[0].priority < best_access.priority:
                    best_access = access_datas[0]
                continue

            priorities = set([x.priority for x in access_datas])

            if len(priorities) == 1:
                current_priority = priorities.pop()
                if current_priority == AccessPriority.VALID_EXTRA:
                    return AccessData(
                        st="right",
                        priority=AccessPriority.VALID_EXTRA,
                        session_id=session_id,
                        group=len(access_datas),
                    )

                if current_priority < best_access.priority:
                    best_access = access_datas[0]
                    if best_access.priority == AccessPriority.VALID_NORMAL:
                        best_access.group = len(access_datas)
                continue

            priority = AccessPriority.INDIVIDUAL
            if priority < best_access.priority and any(
                [x.is_valid() for x in access_datas]
            ):
                best_access = AccessData(
                    st="maybe",
                    priority=priority,
                    session_id=session_id,
                )
                continue

            best_priority = sorted(priorities)[0]
            if best_priority < best_access.priority:
                for access_data in access_datas:
                    if access_data.priority == best_priority:
                        best_access = access_data
                        break

        return best_access

    def mark_as_used(self, session_id, priority):
        if priority == AccessPriority.VALID_NORMAL:
            self.tickets.filter(session_id=session_id).update(
                used=True, used_date=timezone.now()
            )
        elif priority == AccessPriority.VALID_EXTRA:
            update_tickets = []
            for ticket in self.tickets.all():
                ticket.set_extra_session_to_used(session_id)
                update_tickets.append(ticket)
            self.tickets.bulk_update(update_tickets, ["extra_data"])

    @assert_if_not_prefetch_tickets
    def tickets_group_by_sessions(self):
        group_by_session = {}
        for ticket in self.tickets.all():
            if ticket.session_id not in group_by_session:
                group_by_session[ticket.session_id] = [ticket]
            else:
                group_by_session[ticket.session_id].append(ticket)
        return group_by_session

    class Meta:
        ordering = ["-created"]
        verbose_name = _("multipurchase")
        verbose_name_plural = _("multipurchases")

    def __str__(self):
        return self.order


class Ticket(models.Model, BaseTicketModel, BaseTicketMixing, BaseExtraData):
    session = models.ForeignKey(
        Session,
        related_name="tickets",
        verbose_name=_("event"),
        on_delete=models.CASCADE,
    )

    inv = models.OneToOneField(
        InvCode,
        blank=True,
        null=True,
        verbose_name=_("invitation code"),
        on_delete=models.CASCADE,
    )

    order = models.CharField(_("order"), max_length=200, unique=True)
    order_tpv = models.CharField(_("order TPV"), max_length=12, blank=True, null=True)

    tpv_error = models.CharField(_("error TPV"), max_length=200, blank=True, null=True)
    tpv_error_info = models.CharField(
        _("error TPV info"), max_length=200, blank=True, null=True
    )

    payment_method = models.CharField(
        _("payment method"), max_length=10, choices=PAYMENT_TYPES, blank=True, null=True
    )

    created = models.DateTimeField(_("created at"), auto_now_add=True)
    confirmed_date = models.DateTimeField(_("confirmed at"), blank=True, null=True)
    confirmed = models.BooleanField(_("confirmed"), default=False)
    confirm_sent = models.BooleanField(_("confirmation sent"), default=False)
    sold_in_window = models.BooleanField(_("sold in window"), default=False)

    # row-col
    seat = models.CharField(_("seat"), max_length=20, null=True, blank=True)
    seat_layout = models.ForeignKey(
        SeatLayout,
        null=True,
        blank=True,
        verbose_name=_("seat layout"),
        on_delete=models.CASCADE,
    )

    # Form Fields
    email = models.EmailField(_("email"))
    extra_data = models.TextField(_("extra data"), blank=True, null=True)

    mp = models.ForeignKey(
        MultiPurchase,
        related_name="tickets",
        null=True,
        blank=True,
        verbose_name=_("multipurchase"),
        on_delete=models.CASCADE,
    )

    # duplicated data to optimize queries
    session_name = models.CharField(
        _("session name"), max_length=200, null=True, blank=True
    )
    space_name = models.CharField(
        _("space name"), max_length=200, null=True, blank=True
    )
    event_name = models.CharField(
        _("event name"), max_length=200, null=True, blank=True
    )
    price = models.FloatField(_("price"), null=True)
    tax = models.IntegerField(_("tax"), null=True)
    start = models.DateTimeField(_("start date"), null=True)
    end = models.DateTimeField(_("end date"), null=True)
    seat_layout_name = models.CharField(
        _("seat layout name"), max_length=200, null=True, blank=True
    )
    gate_name = models.CharField(_("gate name"), max_length=100, null=True, blank=True)

    # field to control the access
    used = models.BooleanField(_("used"), default=False)
    used_date = models.DateTimeField(_("ticket used date"), blank=True, null=True)

    objects = WriteTicketManager()
    read_objects = ReadTicketManager()

    class Meta:
        ordering = ["-created"]
        verbose_name = _("ticket")
        verbose_name_plural = _("tickets")

    def __str__(self):
        return self.order

    @classmethod
    def prefix(cls) -> str:
        return "T"

    @property
    def wcode(self) -> str:
        return self.window_code()

    @property
    def initials(self):
        space = self.session.space.name
        session = self.session.name

        if self.session.short_name:
            return self.session.short_name
        return _("T") + space[0].upper() + session[0].upper()

    @property
    def text(self):
        data = {
            "space": self.session.space.name.capitalize(),
            "session": self.session.name.capitalize(),
        }
        return _("Ticket %(space)s %(session)s") % data

    @property
    def date(self):
        sstart = self.session.start
        send = self.session.end

        start = formats.date_format(sstart, "l d/m/Y")

        dateformats = {
            "start": _("%(date)s (%(start)s)"),
            "complete": _("%(date)s (%(start)s to %(end)s)"),
            "onlydate": _("%(date)s"),
        }
        strdate = dateformats[self.session.dateformat]

        return strdate % {
            "date": start,
            "start": short_hour(sstart),
            "end": short_hour(send),
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

    @property
    def ticket_window_code(self) -> str:
        return self.mp.ticket_window_code

    def get_gate_name(self):
        return self.gate_name

    def save(self, *args, **kw):
        if self.pk is not None:
            orig = Ticket.objects.get(pk=self.pk)
            confirm = self.confirmed != orig.confirmed
            if orig.used != self.used:
                if self.used:
                    self.used_date = timezone.now()
                else:
                    self.used_date = None
        else:
            confirm = True

        if confirm and self.confirmed:
            self.confirmed_date = timezone.now()

        super().save(*args, **kw)

    def delete(self, *args, **kwargs):
        self.remove_hold_seats()
        super(Ticket, self).delete(*args, **kwargs)

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

    def update_mp_extra_data(self):
        if not self.mp or not self.mp.extra_data:
            return

        data = json.loads(self.mp.extra_data)
        for k, v in data.items():
            self.set_extra_data(k, v)

    def fill_duplicated_data(self):
        self.session_name = self.session.name
        self.space_name = self.space().name
        self.event_name = self.event().name
        self.price = self.session.price
        self.tax = self.session.tax
        self.start = self.session.start
        self.end = self.session.end
        if self.seat_layout:
            self.seat_layout_name = self.seat_layout.name
            if self.seat_layout.gate:
                self.gate_name = self.seat_layout.gate.name

        self.update_mp_extra_data()
        self.save_extra_sessions()

    def get_template(self, session_template: SessionTemplate) -> TicketTemplate:
        if session_template == SessionTemplate.ONLINE:
            return self.session.template

        if session_template == SessionTemplate.WINDOW:
            return self.session.window_template

        raise Exception(_("Not found ticket template"))

    def html_format(
        self,
        session_template: SessionTemplate,
        preview_pdf: bool = False,
        qr_group=None,
    ):
        ticket_template = self.get_template(session_template)
        tpl_child = Template(ticket_template.extra_html)
        qr = self.gen_qr()
        if qr_group is None:
            qr_group = qr
        ctx = Context(
            {
                "ticket": self,
                "qr": qr,
                "qr_group": qr_group,
                "template": ticket_template,
            }
        )
        preview_data = tpl_child.render(ctx)

        template = loader.get_template("tickets/preview.html")
        return template.render(
            {
                "template": ticket_template,
                "preview": preview_data,
                "preview_pdf": preview_pdf,
            }
        )

    def window_code(self):
        """
        ONLMMDDHHMM
        """

        prefix = "ONL"
        postfix = timezone.localtime(self.created).strftime("%m%d%H%M")
        if self.sold_in_window:
            from windows.models import TicketWindowSale

            prefix = TicketWindowSale.objects.values_list(
                "window__code", flat=True
            ).get(purchase__tickets=self)

        return prefix + postfix

    def get_real_price(self):
        if self.sold_in_window:
            return self.get_window_price()
        else:
            return self.get_price()

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
        extra_access_data = self.can_access_extra(session_id, gate_name)
        if extra_access_data.is_valid():
            return extra_access_data

        if self.session_id != session_id:
            priority = AccessPriority.INVALID_SESSION

            if extra_access_data.priority < priority:
                return extra_access_data

            return AccessData(
                st="wrong",
                priority=priority,
                session_id=session_id,
            )

        if self.used:
            priority = AccessPriority.USED

            if extra_access_data.priority < priority:
                return extra_access_data

            return AccessData(
                st="wrong",
                priority=priority,
                session_id=session_id,
                date=self.used_date,
            )

        if gate_name and self.gate_name and self.gate_name != gate_name:
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
        if priority == AccessPriority.VALID_NORMAL:
            self.used = True
            self.used_date = timezone.now()
            self.save()
        elif priority == AccessPriority.VALID_EXTRA:
            self.set_extra_session_to_used(session_id)
            self.save()


class TicketWarning(models.Model):
    name = models.CharField(max_length=50)

    ev = models.ForeignKey(
        Event,
        related_name="warnings",
        verbose_name=_("event"),
        on_delete=models.CASCADE,
    )
    sessions1 = models.ManyToManyField(
        Session, related_name="warnings1", verbose_name=_("sessions1")
    )
    sessions2 = models.ManyToManyField(
        Session, related_name="warnings2", verbose_name=_("sessions2")
    )
    message = models.TextField(_("message"))
    type = models.CharField(
        _("type"), max_length=10, choices=WARNING_TYPES, default="req"
    )

    class Meta:
        verbose_name = _("ticket warning")
        verbose_name_plural = _("ticket warnings")

    def sessions1_ids(self):
        return ",".join(str(s.id) for s in self.sessions1.all())

    def sessions2_ids(self):
        return ",".join(str(s.id) for s in self.sessions2.all())

    def __str__(self):
        return self.name


class TicketSeatHold(models.Model):
    client = models.CharField(_("client"), max_length=20)
    session = models.ForeignKey(
        Session,
        related_name="seat_holds",
        verbose_name=_("session"),
        on_delete=models.CASCADE,
    )
    layout = models.ForeignKey(
        SeatLayout, verbose_name=_("layout"), on_delete=models.CASCADE
    )
    seat = models.CharField(_("seat"), max_length=20, help_text="row-col")
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        _("type"), max_length=2, choices=SEATHOLD_TYPES, default="H"
    )

    class Meta:
        verbose_name = _("ticket seat hold")
        verbose_name_plural = _("ticket seat holds")

    def __str__(self):
        return self.seat


def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


post_save.connect(confirm_email, Ticket)
post_save.connect(confirm_email, MultiPurchase)
