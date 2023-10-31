from typing import Literal

from django.utils import formats, timezone

from access.enums import AccessPriority
from events.models import Session


ST = Literal["right", "maybe", "wrong"]


def short_date(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return formats.date_format(dt, "SHORT_DATETIME_FORMAT")


class AccessData:
    def __init__(self, st: ST, priority: AccessPriority, session_id: int, **kwargs):
        self.st = st
        self.priority = priority
        self.session_id = session_id
        self.session_name = ""
        self.date = ""
        self.gate_name = ""

        if date := kwargs.get("date"):
            self.date = short_date(date)

        self.gate_name = kwargs.get("gate_name", "")
        self.group = kwargs.get("group", None)

    def __cmp__(self, other):
        return self.priority - other.priority

    def __lt__(self, other):
        return self.priority < other.priority

    def set_session(self, sessions_obj: dict[int, Session]):
        self.session_name = sessions_obj.get(self.session_id, "")

    def is_best(self) -> bool:
        return self.priority == AccessPriority.VALID_EXTRA

    def is_valid(self) -> bool:
        return self.st == "right"

    def get_response_data(self):
        data = {
            "session_name": self.session_name,
            "date": self.date,
            "gate_name": self.gate_name,
            "group": self.group,
        }
        return {
            "st": self.st,
            "msg": self.priority.msg(data),
            "msg2": self.priority.msg2(data),
        }
