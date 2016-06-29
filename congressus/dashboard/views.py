from django.shortcuts import render
from django.views.generic import TemplateView

class GeneralView(TemplateView):
    template_name = 'dashboard/general.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(GeneralView, self).get_context_data(*args, **kwargs)
        return ctx

general = GeneralView.as_view()
