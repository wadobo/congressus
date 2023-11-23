from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


def not_contains_spaces(value):
    if " " in value:
        raise ValidationError(_("Spaces are not allowed"))


def validate_phone(value):
    return RegexValidator(r"^\+?[0-9]+$", _("Enter a valid phone"))
