from copy import deepcopy
from datetime import timedelta
from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from random import randint

from access.models import AC_TYPES
from access.models import AccessControl
from access.models import LogAccessControl
from tickets.models import Ticket
from windows.models import PAYMENT_TYPES
from windows.models import TicketWindow
from windows.models import TicketWindowSale


class GeneralView(TemplateView):
    template_name = 'dashboard/general.html'
    DEFAULT_LINE_DATASET = {
        "label": "All",
        "fill": False,
        "lineTension": 0,
        "borderColor": "rgba(0,0,0,1)",
        "borderWidth": 1,
        "pointBorderWidth": 1,
        "pointRadius": 1,
        "scaleStartValue": 0,
        "data": [],
    }
    MAIN_DATASET = deepcopy(DEFAULT_LINE_DATASET)
    MAIN_DATASET['borderWidth'] = 5
    MAIN_DATASET['fill'] = True
    DATA_LINE = {
        "labels": [],
        "datasets": [deepcopy(MAIN_DATASET)]
    }
    INDEX_MAIN = 0
    DEFAULT_PIE_DATASET = {
        "backgroundColor": [],
        "hoverBackgroundColor": [],
        "data": [],
    }
    DATA_PIE = {
        "labels": [],
        "datasets": []
    }

    def dataset_index(self, datasets, name):
        index = 0
        for dataset in datasets:
            if dataset.get('label') == name:
                return index
            index += 1
        return -1

    def get_timesteps_vars(self, timestep='daily'):
        if timestep == 'daily':
            strftime = '%Y-%m-%d'
            delta = timedelta(days=1)
        elif timestep == 'hourly':
            strftime= '%Hh %Y-%m-%d'
            delta = timedelta(hours=1)
        elif timestep == 'minly':
            strftime = '%H:%M %Y-%m-%d'
            delta = timedelta(minutes=1)
        else:
            strftime = '%Y-%m-%d'
            delta = timedelta(days=1)
        return strftime, delta

    def get_access(self, timestep='daily', max=10):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.now()
        min_date = now - delta*max
        res = deepcopy(self.DATA_LINE)

        # Create datasets
        res['datasets'][0]['data'] = [0]*max
        for control in AccessControl.objects.all():
            new_dataset = deepcopy(self.DEFAULT_LINE_DATASET)
            new_dataset['label'] = control.name
            new_dataset['borderColor'] = self.get_random_color()
            new_dataset['data'] = [0]*max
            res['datasets'].append(new_dataset)

        # Create labels
        for l in reversed(range(0, max)):
            date = (now - delta*l).strftime(strftime)
            res.get("labels").append(date)

        # Fill access control
        acs = LogAccessControl.objects.filter(date__gt=min_date).order_by('date')
        for ac in acs:
            date = ac.date.strftime(strftime)
            try:
                index = res.get("labels").index(date)
            except ValueError:
                continue
            extra_index = self.dataset_index(res['datasets'], ac.access_control.name)
            res.get("datasets")[self.INDEX_MAIN].get('data')[index] += 1
            res.get("datasets")[extra_index].get('data')[index] += 1
        return res

    def get_random_color(self):
        rand = []
        for x in range(3):
            rand.append(randint(0, 255))
        return 'rgba(%s,1)' % (','.join(map(str, rand)))

    def get_sales(self, timestep='daily', max=10):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.now()
        min_date = now - delta*max
        res = deepcopy(self.DATA_LINE)

        # Create datasets
        res['datasets'][0]['data'] = [0]*max
        for ticket_window in TicketWindow.objects.all():
            new_dataset = deepcopy(self.DEFAULT_LINE_DATASET)
            new_dataset['label'] = ticket_window.name
            new_dataset['borderColor'] = self.get_random_color()
            new_dataset['data'] = [0]*max
            res['datasets'].append(new_dataset)

        # Create labels
        for l in reversed(range(0, max)):
            date = (now - delta*l).strftime(strftime)
            res.get("labels").append(date)

        # Fill sales
        sales = TicketWindowSale.objects.filter(date__gt=min_date).order_by('date')
        for sale in sales:
            date = sale.date.strftime(strftime)
            try:
                index = res.get("labels").index(date)
            except ValueError:
                continue
            extra_index = self.dataset_index(res['datasets'], sale.window.name)
            res.get("datasets")[self.INDEX_MAIN].get('data')[index] += 1
            res.get("datasets")[extra_index].get('data')[index] += 1
        return res


    def get_pie(self, type='access'):
        res = deepcopy(self.DATA_PIE)
        # Create labels and dataset
        labels = []
        values = []
        if type == 'access':
            labels = [x[0] for x in AC_TYPES]
            values = LogAccessControl.objects.all()
        elif type == 'sale':
            labels = [x[0] for x in PAYMENT_TYPES]
            values = TicketWindowSale.objects.all()

        dataset = deepcopy(self.DEFAULT_PIE_DATASET)
        for label in labels:
            res.get("labels").append(label)
            color = self.get_random_color()
            dataset['backgroundColor'].append(color)
            dataset['hoverBackgroundColor'].append(color)
            if type == 'access':
                value = values.filter(status=label).count()
            elif type == 'sale':
                value = values.filter(payment=label).count()
            dataset['data'].append(value)
        res['datasets'].append(dataset)
        return res


    def get_context_data(self, *args, **kwargs):
        ctx = super(GeneralView, self).get_context_data(*args, **kwargs)
        ctx['ws_server'] = settings.WS_SERVER
        return ctx

    def post(self, request):
        ctx = {}
        ctx['access_log'] = self.get_access('hourly', 20)
        ctx['sales_log'] = self.get_sales('hourly', 20)
        ctx['access_pie_log'] = self.get_pie('access')
        ctx['sales_pie_log'] = self.get_pie('sale')
        return JsonResponse(ctx)
general = csrf_exempt(GeneralView.as_view())
