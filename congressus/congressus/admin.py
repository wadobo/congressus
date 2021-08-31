from django.contrib import admin
from django.db.utils import OperationalError, ProgrammingError
from events.models import Event


class CustomSite(admin.AdminSite):
    def ev(self):
        return Event.objects.get(slug=self.name)


SITES = []
try:  # First migration Event don't exist
    for ev in Event.objects.all().order_by('slug'):
        class EvSite(CustomSite):
            site_header = ev.name
        SITES.append(EvSite(name=ev.slug))
except (ProgrammingError, OperationalError):
    print('SITES no loading')


def custom_inline(inline, slug):
    class CustomInlineAdmin(inline):
        def get_field_queryset(self, db, db_field, request):
            qs = super().get_field_queryset(db, db_field, request)
            if not qs:
                qs = db_field.remote_field.model._default_manager.using(db).all()
            if qs and hasattr(self, 'event_filter_fields'):
                fields = self.event_filter_fields(slug)
                if db_field.name in fields:
                    qs = qs.filter(fields[db_field.name])
            return qs

    return CustomInlineAdmin


def register(model, modeladmin):
    admin.site.register(model, modeladmin)
    for s in SITES:
        if hasattr(modeladmin, 'event_filter'):
            class CustomAdmin(modeladmin):
                EVENT = s.name

                inlines = [custom_inline(i, s.name) for i in modeladmin.inlines]

                def get_field_queryset(self, db, db_field, request):
                    qs = super().get_field_queryset(db, db_field, request)
                    if not qs:
                        qs = db_field.remote_field.model._default_manager.using(db).all()
                    if qs and hasattr(self, 'event_filter_fields'):
                        fields = self.event_filter_fields(self.EVENT)
                        if db_field.name in fields:
                            qs = qs.filter(fields[db_field.name])
                    return qs

                def get_queryset(self, request):
                    return super().event_filter(request, self.EVENT)

            s.register(model, CustomAdmin)
        else:
            s.register(model, modeladmin)

def context_processor(request):
    return {'SITES': SITES}
