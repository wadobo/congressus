# Custom admin sites to be able to show a different admin site for each Event
from django.contrib import admin
from events.models import Event


class CustomSite(admin.AdminSite):
    def ev(self):
        return Event.objects.get(slug=self.name)


SITES = []
for ev in Event.objects.all():
    class EvSite(CustomSite):
        site_header = ev.name
    SITES.append(EvSite(name=ev.slug))

def register(model, modeladmin):
    admin.site.register(model, modeladmin)
    for s in SITES:
        # TODO: modify the modeladmin to use  the custom queryset
        # for this event
        if hasattr(modeladmin, 'event_filter'):
            class CustomAdmin(modeladmin):
                EVENT = s.name

                def get_queryset(self, request):
                    return super().event_filter(request, self.EVENT)

            s.register(model, CustomAdmin)
        else:
            s.register(model, modeladmin)

def context_processor(request):
    return {'SITES': SITES}
