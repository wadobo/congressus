from __future__ import annotations

from typing import TYPE_CHECKING

from django.template import loader
from django.utils.translation import gettext as _

if TYPE_CHECKING:
    from events.models import TicketTemplate


class TicketHTML:
    template_name = "tickets/preview.html"

    def __init__(self, tickets, is_invitation=False, template=None):
        self.tickets = tickets
        self.is_invitation = is_invitation
        self.template = template if template is not None else self._calc_template()

        if not self.template:
            raise Exception(_('Not found ticket template'))

    def _calc_template(self) -> TicketTemplate:
        if self.is_invitation:
            return self.tickets[0].type.template
        return self.ticket[0].session.template

    def generate(self, asbuf: bool = False):
        template = loader.get_template(self.template_name)
        context = {
            "template": self.template,
            "tickets": self.tickets,
        }
        return template.render(context)
