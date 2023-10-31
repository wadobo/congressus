from enum import Enum

from django.utils.translation import gettext_lazy as _


class AccessPriority(Enum):
    VALID_EXTRA = 1, "Ok: {session_name}", "G {group}"
    VALID_NORMAL = 2, "Ok: {session_name}", "G {group}"
    INDIVIDUAL = 3, _("Some used: read individually"), ""
    INVALID_GATE = 4, _("{session_name} - Gate: {gate_name}"), ""
    HOUR_TOO_SOON = 5, _("Too soon, wait until {date}"), ""
    HOUR_EXPIRED = 6, _("Expired, ended at {date}"), ""
    USED = 7, _("Used: {date}"), "{session_name}"
    INVALID_SESSION = 8, "{session_name}", ""
    INVALID_ORDER = 9, _("Not exists"), ""
    UNKNOWN = 10, "Unknown", ""

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] < other.value[0]
        return NotImplemented

    def is_valid(self):
        return self in [AccessPriority.VALID_EXTRA, AccessPriority.VALID_NORMAL]

    def msg(self, data):
        return self.value[1].format(**data)

    def msg2(self, data):
        if self.is_valid():
            if data.get("group"):
                return self.value[2].format(**data)
            else:
                return ""
        return self.value[2].format(**data)
