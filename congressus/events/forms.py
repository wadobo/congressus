from django import forms

from events.models import TicketTemplate


class TicketTemplateForm(forms.ModelForm):
    class Meta:
        model = TicketTemplate
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        monospace_style = "font: 1em 'typewriter', monospace;"
        self.fields["extra_style"].widget.attrs["style"] = monospace_style
        self.fields["extra_js"].widget.attrs["style"] = monospace_style
        self.fields["extra_html"].widget.attrs["style"] = monospace_style
