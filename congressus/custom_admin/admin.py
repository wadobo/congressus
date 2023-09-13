from django.contrib import admin
from django.template.response import TemplateResponse

from events.models import Event


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom-index.html"

    def index(self, request, extra_context=None):
        if request.method == "POST":
            current_event = request.POST.dict().get("event_name", "all")
            request.session["current_event"] = current_event
        else:
            current_event = request.session.get("current_event", "all")

        event_names = Event.read_objects.choices()
        for id, name in event_names:
            if current_event == id:
                self.site_header = name
                break

        app_list = self.get_app_list(request)

        context = {
            **self.each_context(request),
            "title": self.index_title,
            "subtitle": None,
            "app_list": app_list,
            **(extra_context or {}),
            "event_names": event_names,
            "current_event": current_event,
        }

        request.current_app = self.name

        return TemplateResponse(
            request, self.index_template or "admin/index.html", context
        )
