import random
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from PyPDF2 import PdfFileMerger


def concat_pdf(files):
    _buffer = BytesIO()
    fm = PdfFileMerger()
    for f in files:
        fm.append(f)
    fm.write(_buffer)
    fm.close()

    pdf = _buffer.getvalue()
    _buffer.close()
    return pdf


def get_ticket_format(mp, pf=None, attachment=True):
    """ With a list of invitations or invitations,generate ticket output """
    from events.models import TicketTemplate
    if pf == 'csv':
        csv = []
        if hasattr(mp, 'all_tickets'): # is MultiPurchase
            for i, ticket in enumerate(mp.all_tickets()):
                csv.append("%s, %s, %s" % (i+1, ticket.order, ticket.session_name))
        else: # is Ticket
            csv.append("%s, %s, %s" % (i+1, mp.order, mp.session_name))
        response = HttpResponse(content_type='application/csv')
        response['Content-Disposition'] = 'filename="invs.csv"'
        response.write('\n'.join(csv))

    else:
        if pf is None:
            template = None
        else:
            template = TicketTemplate.objects.filter(pk=pf).first()
        pdf = mp.generate_pdf(template)
        response = HttpResponse(content_type='application/pdf')
        fname = 'filename="tickets.pdf"'
        if attachment:
            fname = 'attachment; ' + fname
        response['Content-Disposition'] = fname
        response.write(pdf)

    return response


def check_free_seats(sessions, res):
    # TODO: only look fisrt session
    from events.models import SeatLayout
    session = sessions.first()
    for k in res.keys():
        layout = SeatLayout.objects.get(name=k)
        layout_maps = layout.real_rows()
        for v in res.get(k)[:]:
            col, row = v.split('-')
            try:
                st = layout_maps[int(col)-1, int(row)-layout.column_start_number]
                if st == '_':
                    res[k].remove(v)
            except IndexError:
                res[k].remove(v)
            if session.seat_holds.filter(layout=layout, seat=v).exists():
                res[k].remove(v)
    return res


def get_seats_by_str(sessions, string):
    """ String format: 'C1[1-1,1-3]; C1[2-1:2-10]; C1[]' """
    res = {} # {'C1': ['1-1', '1-2']}, ...
    string = string.replace(' ', '')
    layouts = string.split(";")
    for layout in layouts:
        open_bracket = layout.find('[')
        close_bracket = layout.find(']')
        if open_bracket == -1 or close_bracket == -1:
            raise 'invalid format'
        lay = layout[:open_bracket]
        seats = layout[open_bracket+1:close_bracket]
        if seats:
            for seat in seats.split(','):
                if seat.find(':') == -1:
                    col, row = seat.split('-')
                    if not col or not row:
                        raise 'invalid format'
                    row_seat = [seat]
                else:
                    ini_seat, end_seat = seat.split(':')
                    ini_col, ini_row = ini_seat.split('-')
                    end_col, end_row = end_seat.split('-')
                    row_seat = []
                    for col in range(int(ini_col), int(end_col)+1):
                        for row in range(int(ini_row), int(end_row)+1):
                            row_seat.append('%s-%s' % (col, row))
                if lay in res.keys():
                    res[lay] += row_seat
                else:
                    res.update({lay: row_seat})
    # we don't check for free seats, we'll return always the array
    # res = check_free_seats(sessions, res)
    return res


def search_seats(session, amount):
    layouts = []
    row_rand = 0
    if session.autoseat_mode == 'ASC':
        layouts = session.space.seat_map.layouts.all().order_by('name')
    elif session.autoseat_mode == 'DESC':
        layouts = session.space.seat_map.layouts.all().order_by('-name')
    elif session.autoseat_mode == 'RANDOM':
        layouts = list(session.space.seat_map.layouts.all())
        random.shuffle(layouts)
        row_rand = settings.ROW_RAND * 1
    elif session.autoseat_mode.startswith("LIST"):
        autoseats = session.autoseat_mode.split(':')[1]
        for layout in autoseats.split(','):
            l = session.space.seat_map.layouts.filter(name=layout.strip()).first()
            if l:
                layouts.append(l)
    else:
        layouts = session.space.seat_map.layouts.all().order_by('name')

    best_avail = None
    if row_rand:
        row_rand = random.randint(0, row_rand)
    for layout in layouts:
        hold_seats = session.seats_holded(layout)
        avail = layout.contiguous_seats(amount, hold_seats, layout.column_start_number, row_rand=row_rand)
        if not avail:
            continue
        best_avail = {
            'layout': layout,
            'row': avail.get('row'),
            'col_ini': avail.get('col_ini'),
            'col_end': avail.get('col_end')
        }
        break
    seats = []
    if best_avail:
        for col in range(best_avail.get('col_ini'), best_avail.get('col_end')):
            seats.append({
                "session": session.id,
                "layout": best_avail['layout'].id,
                "row": best_avail['row'],
                "col": col+best_avail['layout'].column_start_number-1})
    return seats
