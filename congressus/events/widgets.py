from django import forms
from django.utils.safestring import mark_safe


class HTMLWidget(forms.Widget):
    def render(self, name, *args, **kwargs):
        return mark_safe(name)