import datetime
import json
import os

from django.db.models import Count
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from .models import SingleRowTail, SingleRowConfig
from events.models import Event
from windows.models import TicketWindow



class SingleRow(View):

    def get(self, request, *args, **kwargs):
        data = {}
        params = request.GET.dict()
        event = get_object_or_404(Event, id=params.get('event_id'))

        config, crated = SingleRowConfig.objects.get_or_create(event=event)
        data['config'] = {
            "extra_text": config.extra_text,
            "last_window": config.last_window.name if config.last_window else "",
        }

        tail = SingleRowTail.objects.filter(event=event)
        if not tail.exists():
            return JsonResponse(data, status=404)
        else:
            if config.last_window:
                tail_exclude = tail.exclude(window=config.last_window)
                if tail_exclude.exists():
                    tail = tail_exclude
            sr = tail.first()

            config.last_window = sr.window
            config.save()

            sr.delete()

        tw_name = sr.window.name
        tw_num = sr.window.code
        data['name'] = tw_name
        data['tw_name'] = tw_name
        data['tw_num'] = tw_num
        data['url'] = sr.voice_url()
        data['position'] = sr.window.singlerow_pos

        return JsonResponse(data)

    def get_singlerow_tails(self, event):
        singlerow_tails = SingleRowTail.objects.filter(event=event)\
                .values('window__name').annotate(total=Count('window'))\
                .order_by('total').values_list('window__name', 'total')
        out = ''
        for sr in singlerow_tails:
            out += '<span class="window-debug">{0}: {1}</span>'.format(sr[0], sr[1])
        return out

    def post(self, request, *args, **kwargs):
        data = {'debug': ''}
        params = request.POST.dict()
        event = get_object_or_404(Event, id=params.get('event_id'))
        config, created = SingleRowConfig.objects.get_or_create(event=event)
        staff = params.get('staff', False)
        if staff:
            data['debug'] = self.get_singlerow_tails(event=event)

        window_slug = params.get('window_slug')
        command = params.get('command')

        tw = get_object_or_404(TicketWindow, slug=window_slug, event=event)

        if command == 'open' and not tw.singlerow:
            tw.singlerow = True
            tw.save()
            data['window_status'] = _('Opened')
            for i in range(2):
                sr = SingleRowTail(event=tw.event, window=tw)
                sr.save()
        elif command == 'close' and tw.singlerow:
            tw.singlerow = False
            tw.save()
            data['window_status'] = _('Closed')
            SingleRowTail.objects.filter(window=tw).delete()
        elif command == 'request' and tw.singlerow:
            if config.waiting.filter(id=tw.id).exists():
                config.waiting.remove(tw)
            else:
                sr = SingleRowTail(event=tw.event, window=tw)
                sr.save()
        elif command == 'wait' and tw.singlerow:
            last = SingleRowTail.objects.filter(window=tw).last()
            if last:
                last.delete()
            else:
                config.waiting.add(tw)
        return JsonResponse(data)

singlerow = csrf_exempt(SingleRow.as_view())


class SingleRowView(TemplateView):
    template_name = 'singlerow/main.html'

    def get_context_data(self, *args, **kwargs):
        ev = self.kwargs.get('ev')
        event = get_object_or_404(Event, slug=ev)
        ctx = super().get_context_data(*args, **kwargs)
        ctx['event'] = event
        ctx['seconds'] = settings.SINGLEROW_MS
        return ctx

singlerow_view = SingleRowView.as_view()
