from copy import deepcopy
from datetime import timedelta
from datetime import datetime
from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
# Django 1.10: instead .extra (deprecated soon)
#from django.db.models.functions import TruncDay
from django.db import connection
from django.db.models import Count
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Sum
from django.db.models import Value
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from random import randint

from .models import CHARTS
from .models import Dashboard
from access.models import AC_TYPES
from access.models import AccessControl
from access.models import LogAccessControl
from events.models import Event
from events.models import Session
from tickets.models import MultiPurchase
from tickets.models import Ticket
from windows.models import PAYMENT_TYPES
from windows.models import TicketWindow
from windows.models import TicketWindowSale


class DashboardsView(TemplateView):
    template_name = 'dashboard/list.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ev = get_object_or_404(Event, slug=kwargs.get('ev', ''))
        dashs = ev.dashboard_set.all()

        ctx['ev'] = ev
        ctx['dashs'] = dashs
        ctx['menuitem'] = 'dashboard'
        return ctx
dlist = staff_member_required(DashboardsView.as_view())


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

    def get_timesteps_vars(self, timestep):
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

    def get_access(self, timestep, max):
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

    def get_sales_online(self, timestep, max):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.now()
        min_date = now - delta*max
        res = deepcopy(self.DATA_LINE)

        # Create datasets
        res['datasets'][0]['data'] = [0]*max
        for session in Session.objects.all():
            new_dataset = deepcopy(self.DEFAULT_LINE_DATASET)
            new_dataset['label'] = session.space.name + "  " + session.name
            new_dataset['borderColor'] = self.get_random_color()
            new_dataset['data'] = [0]*max
            res['datasets'].append(new_dataset)

        # Create labels
        for l in reversed(range(0, max)):
            date = (now - delta*l).strftime(strftime)
            res.get("labels").append(date)

        # Fill sales online
        mps = MultiPurchase.objects.filter(created__gt=min_date, confirmed=True).order_by('created')
        for mp in mps:
            date = mp.created.strftime(strftime)
            for ticket in mp.all_tickets():
                try:
                    index = res.get("labels").index(date)
                except ValueError:
                    continue
                extra_index = self.dataset_index(res['datasets'], ticket.session.space.name + "  " + ticket.session.name)
                res.get("datasets")[self.INDEX_MAIN].get('data')[index] += 1
                res.get("datasets")[extra_index].get('data')[index] += 1
        return res


    def get_sales(self, timestep, max):
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


    def get_pie(self, type, timestep, max):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.now()
        min_date = now - delta*max
        res = deepcopy(self.DATA_PIE)
        # Create labels and dataset
        labels = []
        values = []
        if type == 'access':
            labels = [x[0] for x in AC_TYPES]
            values = LogAccessControl.objects.filter(date__gt=min_date)
        elif type == 'sale':
            labels = [x[0] for x in PAYMENT_TYPES]
            values = TicketWindowSale.objects.filter(date__gt=min_date)

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


    def get_pie_sales_online(self, timestep, max):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.now()
        min_date = now - delta*max
        res = deepcopy(self.DATA_PIE)
        # Create labels and dataset
        labels = []
        values = []

        labels = [
                {'confirmed': False, 'name': "F", 'color': 'rgba(255,0,0,1)'},
                {'confirmed': True, 'name': "T", 'color': 'rgba(0,255,0,1)'}
        ]
        colors = []

        values = MultiPurchase.objects.filter(created__gt=min_date)

        dataset = deepcopy(self.DEFAULT_PIE_DATASET)
        for label in labels:
            res.get("labels").append(label.get('name'))
            color = label.get('color')
            dataset['backgroundColor'].append(color)
            dataset['hoverBackgroundColor'].append(color)
            value = values.filter(confirmed=label.get('confirmed')).count()
            dataset['data'].append(value)
        res['datasets'].append(dataset)
        return res


    def get_context_data(self, *args, **kwargs):
        ctx = super(GeneralView, self).get_context_data(*args, **kwargs)
        ctx['ws_server'] = settings.WS_SERVER
        ctx['ev'] = self.kwargs['ev']
        ctx['dash'] = self.kwargs['dash']
        return ctx

    def get_chart(self, type_chart, timestep=settings.TIMESTEP_CHART, max=settings.MAX_STEP_CHART):
        title = ''
        for k, v in CHARTS:
            if k == type_chart:
                title = str(v)

        if type_chart == 'os_c':
            chart = self.get_sales_online(timestep, max)
        elif type_chart == 'ws_c':
            chart = self.get_sales(timestep, max)
        elif type_chart == 'a_c':
            chart = self.get_access(timestep, max)
        elif type_chart == 'os_p':
            chart = self.get_pie_sales_online(timestep, max)
        elif type_chart == 'ws_p':
            chart = self.get_pie('sale', timestep, max)
        elif type_chart == 'a_p':
            chart = self.get_pie('access', timestep, max)
        else:
            chart = None
        tdata, tchart = type_chart.split('_')
        return {
                'data': chart,
                'type_data': tdata,
                'title': title,
                'type_chart': tchart
        }

    def post(self, request, ev, dash):
        ctx = {}
        ctx['charts'] = []
        ev = get_object_or_404(Event, slug=ev)
        dashboard = get_object_or_404(Dashboard, event=ev, slug=dash)
        for chart in dashboard.charts.all():
            ctx['charts'].append(self.get_chart(chart.type, chart.timestep, chart.max_steps))
        return JsonResponse(ctx)
general = csrf_exempt(GeneralView.as_view())


class ReportView(TemplateView):
    template_name = 'dashboard/generate_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(ReportView, self).get_context_data(*args, **kwargs)
        ev = self.kwargs['ev']
        self.ev = get_object_or_404(Event, slug=ev)
        self.windows = self.ev.windows.all()
        self.sessions = self.ev.get_sessions()

        ctx['ws_server'] = settings.WS_SERVER
        ctx['ev'] = self.ev
        ctx['sessions'] = self.sessions
        ctx['windows'] = self.windows
        ctx['menuitem'] = 'report'

        return ctx

    def get_online_datas(self, sessions, report_type):
        tickets = Ticket.objects.filter(confirmed=True, sold_in_window=False, session__in=sessions)
        return tickets.values('session__name', 'session__space__name')\
                .annotate(
                        amount=Count('pk'),
                        total_price=Sum('price'),
                        price_without_iva=Sum(F('price')/(1+F('tax')/100.0), output_field=FloatField()))\
                .order_by('session__start')

    def get_window_sale_datas(self, sessions, report_type):
        tickets = Ticket.objects.filter(confirmed=True, sold_in_window=True)
        tickets = tickets.filter(session__in=sessions)
        return tickets.values('session__name', 'session__space__name')\
                .annotate(
                        amount=Count('pk'),
                        total_price=Sum('price'),
                        price_without_iva=Sum(F('price')/(1+F('tax')/100.0), output_field=FloatField()))\
                .order_by('session__start')

    def get_datas(self, window_sales, onlines, sessions, report_type):
        general_table = []
        specific_tables = []
        general = {
                'online': {'amount': 0, 'p_iva': 0, 'p_noiva': 0},
                'window_sale': {'amount': 0, 'p_iva': 0, 'p_noiva': 0},
        }

        if report_type in ['online', 'general']:
            specific_tables.append({'title': 'Online', 'datas': []})
            last_spec_table = specific_tables[-1]['datas']
            last_spec_table.append(['tickets of', '', 'total'])
            for o in onlines:
                general['online']['p_iva'] += o.get('total_price')
                general['online']['p_noiva'] += o.get('price_without_iva')
                general['online']['amount'] += o.get('amount')
                last_spec_table.append([o.get('session__name'), '#', o.get('amount')])
                last_spec_table.append(['€ / € sin IVA', '%.2f / %.2f' % (o.get('total_price'), o.get('price_without_iva'))])

        if report_type in ['window_sale', 'general']:
            specific_tables.append({'title': 'Window sale', 'datas': []})
            last_spec_table = specific_tables[-1]['datas']
            last_spec_table.append(['tickets of', '', 'total'])
            for w in window_sales:
                general['window_sale']['p_iva'] += w.get('total_price')
                general['window_sale']['p_noiva'] += w.get('price_without_iva')
                general['window_sale']['amount'] += w.get('amount')
                last_spec_table.append([w.get('session__name'), '#', w.get('amount')])
                last_spec_table.append(['€ / € sin IVA', '%.2f / %.2f' % (w.get('total_price'), w.get('price_without_iva'))])

        general_table = [
                ['', 'Online', 'Window sale', 'Total'],
                [
                    '#',
                    general['online']['amount'],
                    general['window_sale']['amount'],
                    general['online']['amount'] + general['window_sale']['amount']
                ],
                [
                    '€/€ sin IVA',
                    '%.2f / %.2f' % (general['online']['p_iva'], general['online']['p_noiva']),
                    '%.2f / %.2f' % (general['window_sale']['p_iva'], general['window_sale']['p_noiva']),
                    '%.2f / %.2f' % (general['online']['p_iva'] + general['window_sale']['p_iva'],
                                 general['online']['p_noiva'] + general['window_sale']['p_noiva'])
                ]
        ]
        # Removed some datas if not neccesary
        if report_type in ['online', 'window_sale']:
            for row in general_table:
                del row[-1] # Total
                if report_type == 'online':
                    del row[2]
                else:
                    del row[1]

        return general_table, specific_tables

    def get_arqueo(self, sessions, window_sales):
        mps = TicketWindowSale.objects.filter(window__in=window_sales).values_list('purchase', flat=True)
        tickets = Ticket.objects.filter(confirmed=True, sold_in_window=True, session__in=sessions, mp__in=mps)
        return tickets.values('session__name', 'session__space__name')\
                .annotate(
                        amount=Count('pk'),
                        total_price=Sum('price'),
                        price_without_iva=Sum(F('price')/(1+F('tax')/100.0), output_field=FloatField()))\
                .order_by('session__start')

    def gen_arqueo_table(self, datas):
        table = []
        table.append(['', '', 'total'])
        for col in datas:
            table.append([col.get('session__name'), '#', col.get('amount')])
            table.append(['€ / € sin IVA', '%.2f / %.2f' % (col.get('total_price'), col.get('price_without_iva'))])
        return table

    def post(self, request, ev):
        event = get_object_or_404(Event, slug=ev)
        ctx = {}
        ctx['ev'] = get_object_or_404(Event, slug=ev)
        ctx['sessions'] = Session.objects.all()
        ctx['windows'] = TicketWindow.objects.all()
        report_type = request.POST.get('type')
        ctx['report_type'] = report_type

        if report_type != 'arqueo':
            window_sales = self.get_window_sale_datas(report_type)
            sessions = self.get_sessions(request, report_type)
            onlines = self.get_online_datas(sessions, report_type)
            gtable, stables = self.get_datas(window_sales, onlines, sessions, report_type)
            ctx['general_table'] = gtable
            ctx['specific_tables'] = stables
        else:
            sessions = request.POST.getlist('scheck')
            window_sales = request.POST.getlist('wcheck')
            sessions = map(int, sessions)
            window_sales = map(int, window_sales)
            datas = self.get_arqueo(sessions, window_sales)
            arqueo_table = self.gen_arqueo_table(datas)
            ctx['arqueo_table'] = arqueo_table

        return render(request, self.template_name, ctx)

report = csrf_exempt(staff_member_required(ReportView.as_view()))


class GeneralReportView(ReportView):
    template_name = 'dashboard/general_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        report_type = 'general'
        ctx['report_type'] = report_type

        window_sales = self.get_window_sale_datas(self.sessions, report_type)
        onlines = self.get_online_datas(self.sessions, report_type)
        gtable, stables = self.get_datas(window_sales, onlines, self.sessions, report_type)
        ctx['general_table'] = gtable
        ctx['specific_tables'] = stables

        return ctx
report_general = staff_member_required(GeneralReportView.as_view())

class WindowReportView(ReportView):
    template_name = 'dashboard/general_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        report_type = 'window_sale'
        ctx['report_type'] = report_type

        window_sales = self.get_window_sale_datas(self.sessions, report_type)
        onlines = None
        gtable, stables = self.get_datas(window_sales, onlines, self.sessions, report_type)
        ctx['general_table'] = gtable
        ctx['specific_tables'] = stables

        return ctx
report_window = staff_member_required(WindowReportView.as_view())

class OnlineReportView(ReportView):
    template_name = 'dashboard/online_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        report_type = 'online'
        ctx['report_type'] = report_type

        start_date = self.request.GET.get('start-date')
        end_date = self.request.GET.get('end-date')

        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y").date()
            end_date = datetime.strptime(end_date, "%d-%m-%Y").date()
            self.sessions = self.sessions.filter(start__range=(start_date, end_date))

        window_sales = None
        onlines = self.get_online_datas(self.sessions, report_type)
        gtable, stables = self.get_datas(window_sales, onlines, self.sessions, report_type)
        ctx['general_table'] = gtable
        ctx['specific_tables'] = stables

        return ctx
report_online = staff_member_required(OnlineReportView.as_view())

class CountReportView(ReportView):
    template_name = 'dashboard/count_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        report_type = 'arqueo'
        ctx['report_type'] = report_type
        ctx['spaces'] = self.ev.spaces.all()

        request = self.request
        sessions = request.GET.getlist('scheck')
        window_sales = request.GET.getlist('wcheck')
        sessions = map(int, sessions)
        window_sales = map(int, window_sales)
        datas = self.get_arqueo(sessions, window_sales)
        arqueo_table = self.gen_arqueo_table(datas)
        ctx['arqueo_table'] = arqueo_table

        return ctx
report_count = staff_member_required(CountReportView.as_view())


class ReportListView(TemplateView):
    template_name = 'dashboard/list_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ev = get_object_or_404(Event, slug=kwargs.get('ev', ''))
        ctx['ev'] = ev
        return ctx

report_list = staff_member_required(ReportListView.as_view())
