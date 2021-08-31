import itertools
from copy import deepcopy
from datetime import timedelta
from datetime import datetime
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
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
    DEFAULT_BAR_DATASET = {
        "label": "",
        "backgroundColor": [],
        "borderColor": [],
        "borderWidth": 2,
        "data": [],
    }
    DATA_PIE = {
        "labels": [],
        "datasets": []
    }
    DATA_BAR = deepcopy(DATA_PIE)

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
        now = timezone.localtime(timezone.now())
        min_date = now - delta*max
        res = deepcopy(self.DATA_LINE)

        # Create datasets
        res['datasets'][0]['data'] = [0]*max
        for control in AccessControl.objects.all():
            new_dataset = deepcopy(self.DEFAULT_LINE_DATASET)
            new_dataset['label'] = control.slug
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
            date = timezone.localtime(ac.date).strftime(strftime)
            try:
                index = res.get("labels").index(date)
            except ValueError:
                continue
            extra_index = self.dataset_index(res['datasets'], ac.access_control.slug)
            res.get("datasets")[self.INDEX_MAIN].get('data')[index] += 1
            res.get("datasets")[extra_index].get('data')[index] += 1
        return res

    def get_random_color(self, extra_alpha=False):
        rand = []
        for x in range(3):
            rand.append(randint(0, 255))
        if extra_alpha:
            return 'rgba(%s,1)' % (','.join(map(str, rand))), 'rgba(%s,0.2)' % (','.join(map(str, rand)))
        else:
            return 'rgba(%s,1)' % (','.join(map(str, rand)))

    def get_sales_online(self, timestep, max):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.localtime(timezone.now())
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
            date = timezone.localtime(mp.created).strftime(strftime)
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
        now = timezone.localtime(timezone.now())
        min_date = now - delta*max
        res = deepcopy(self.DATA_LINE)

        # Create datasets
        res['datasets'][0]['data'] = [0]*max
        for ticket_window in TicketWindow.objects.all():
            new_dataset = deepcopy(self.DEFAULT_LINE_DATASET)
            new_dataset['label'] = ticket_window.slug
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
            date = timezone.localtime(sale.date).strftime(strftime)
            try:
                index = res.get("labels").index(date)
            except ValueError:
                continue
            extra_index = self.dataset_index(res['datasets'], sale.window.slug)
            res.get("datasets")[self.INDEX_MAIN].get('data')[index] += 1
            res.get("datasets")[extra_index].get('data')[index] += 1
        return res


    def get_pie(self, type, timestep, max):
        strftime, delta = self.get_timesteps_vars(timestep)
        now = timezone.localtime(timezone.now())
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
        now = timezone.localtime(timezone.now())
        min_date = now - delta*max
        res = deepcopy(self.DATA_PIE)
        # Create labels and dataset
        labels = []
        values = []

        labels = [
                {'confirmed': False, 'name': "F", 'color': 'rgba(255,0,0,1)'},
                {'confirmed': True, 'name': "T", 'color': 'rgba(0,255,0,1)'}
        ]
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

    def get_bar(self, type, timestep, max):
        strftime, delta = self.get_timesteps_vars(timestep)
        res = deepcopy(self.DATA_BAR)

        # Create labels and dataset
        datas = TicketWindow.objects.values_list('slug', 'cash').filter(event=self.ev).order_by('slug')

        dataset = deepcopy(self.DEFAULT_BAR_DATASET)
        dataset['label'] = self.ev.slug
        for name, cash in datas:
            res.get("labels").append(name)
            color, alpha = self.get_random_color(True)
            dataset['borderColor'].append(color)
            dataset['backgroundColor'].append(alpha)
            dataset['data'].append(cash)
        res['datasets'].append(dataset)
        return res


    def get_context_data(self, *args, **kwargs):
        ctx = super(GeneralView, self).get_context_data(*args, **kwargs)
        ctx['ws_server'] = settings.WS_SERVER
        ctx['ev'] = self.kwargs['ev']
        ctx['dash'] = self.kwargs['dash']
        dash = Dashboard.objects.filter(name=ctx['dash']).first()
        if dash:
            ctx['num_cols'] = str(12 / int(dash.num_cols))
        else:
            ctx['num_cols'] = '12'
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
        elif type_chart == 'ws_b':
            chart = self.get_bar('sale', timestep, max)
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
        self.ev = ev
        dashboard = get_object_or_404(Dashboard, event=ev, slug=dash)
        for chart in dashboard.charts.all():
            ctx['charts'].append(self.get_chart(chart.type, chart.timestep, chart.max_steps))
        return JsonResponse(ctx)
general = csrf_exempt(GeneralView.as_view())


class ReportView(TemplateView):
    template_name = 'dashboard/generate_report.html'

    def sessions_grouped(self, sessions):
        g = itertools.groupby(sessions, lambda x: x.name)
        g = [(n, list(l)) for n, l in g]
        return g

    def get_days(self):
        days = set()
        q = self.sessions.extra({'date':"date(start)"}).values('date')
        for d in q:
            if type(d) == str:
                args = d['date'].split('-')
                args = map(int, args)
            else:
                d1 = d['date']
                args = (d1.year, d1.month, d1.day)
            day = timezone.make_aware(datetime(*args))
            days.add(day)
        days = sorted(list(days))
        return days

    def get_context_data(self, *args, **kwargs):
        ctx = super(ReportView, self).get_context_data(*args, **kwargs)
        ev = self.kwargs['ev']
        self.ev = get_object_or_404(Event, slug=ev)
        self.windows = self.ev.windows.all()
        self.sessions = self.ev.get_sessions()
        self.spaces = self.ev.spaces.all()

        ctx['ws_server'] = settings.WS_SERVER
        ctx['ev'] = self.ev
        ctx['spaces'] = self.spaces
        ctx['sessions'] = self.sessions
        ctx['windows'] = self.windows
        ctx['menuitem'] = 'report'

        return ctx


class GeneralReportView(ReportView):
    template_name = 'dashboard/general_report.html'
    window = False

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['online_windows'] = TicketWindow.objects.filter(event=self.ev, online=True)
        ctx['local_windows'] = TicketWindow.objects.filter(event=self.ev, online=False)
        ctx['all_windows'] = TicketWindow.objects.filter(event=self.ev)

        days = self.get_days()

        ctx['session_days'] = [(d, ) for d in days]
        ctx['window'] = self.window
        ctx['sessions_grouped'] = self.sessions_grouped(self.sessions)

        return ctx
report_general = staff_member_required(GeneralReportView.as_view())


class WindowReportView(GeneralReportView):
    window = True
report_window = staff_member_required(WindowReportView.as_view())


class OnlineReportView(ReportView):
    template_name = 'dashboard/online_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['online_windows'] = TicketWindow.objects.filter(event=self.ev, online=True)
        ctx['local_windows'] = TicketWindow.objects.filter(event=self.ev, online=False)

        start_date = self.request.GET.get('start-date')
        end_date = self.request.GET.get('end-date')

        if start_date and end_date:
            str_format = "%d-%m-%Y"
            if start_date.find("/") > 0:
                str_format = str_format.replace("-", "/")

            start_date = datetime.strptime(start_date, str_format).date()
            end_date = datetime.strptime(end_date, str_format).date()
            self.sessions = self.sessions.filter(start__range=(start_date, end_date))

            delta = timedelta(days=1)
            d = start_date
            days = []
            while d <= end_date:
                days.append(d)
                d = d + delta
            ctx['sdate'] = start_date
            ctx['edate'] = end_date
            ctx['days'] = days

        days = self.get_days()
        delta = timedelta(days=1)

        ctx['session_days'] = [(d, self.sessions.filter(start__range=(d, d+delta))) for d in days]
        ctx['sessions_grouped'] = self.sessions_grouped(self.sessions)

        return ctx
report_online = staff_member_required(OnlineReportView.as_view())


class CountReportView(ReportView):
    template_name = 'dashboard/count_report.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        query = self.request.GET.get('query', '')
        if query:
            days = self.request.GET.getlist('scheck')
            windows = self.request.GET.getlist('wcheck')

            days = [timezone.make_aware(datetime.strptime(d, "%Y-%m-%d")) for d in days]
            self.windows = self.windows.filter(pk__in=windows)
            ctx['selected_sessions'] = self.sessions
            ctx['selected_days'] = days
            ctx['selected_windows'] = self.windows

            ctx['count_days'] = days
            ctx['sessions_grouped'] = self.sessions_grouped(self.sessions)

        session_days = self.get_days()
        delta = timedelta(days=1)
        ctx['session_days'] = [(d, self.sessions.filter(start__range=(d, d+delta))) for d in session_days]

        ctx['query'] = query

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
