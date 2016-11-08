from django.conf import settings
from django.http import HttpResponse

from tickets.utils import concat_pdf
from tickets.utils import generate_pdf


def gen_csv_from_generator(ig, numbered=True, string=True):
    csv = []
    name = ig.type.name
    for i, inv in enumerate(ig.invitations.all()):
        line = '%s, %s' % (inv.order, name)
        if numbered:
            line = ('%d,' % (i + 1)) + line
        if inv.seat_layout and inv.seat:
            row, col = inv.seat.split('-')
            col = int(col) + inv.seat_layout.column_start_number - 1
            line += ', %s, %s, %s' % (inv.seat_layout.gate, row, col)
        csv.append(line)

    if string:
        return '\n'.join(csv)

    return csv


def gen_csv_from_generators(igs):
    csv = []
    for ig in igs:
        csv += gen_csv_from_generator(ig, numbered=False, string=False)

    out = []
    for i, line in enumerate(csv):
        out.append(('%d ' % (i + 1)) + line)

    return '\n'.join(out)


def gen_pdf(igs):
    from .models import Invitation
    files = []
    for inv in Invitation.objects.filter(generator__in=igs):
        files.append(generate_pdf(inv, asbuf=True, inv=True))
    return concat_pdf(files)


def gen_invs_pdf(invs):
    files = []
    for inv in invs:
        files.append(generate_pdf(inv, asbuf=True, inv=True))
    return concat_pdf(files)


def get_ticket_format(invs, pf):
    """ With a list of invitations or invitations,generate ticket output """
    if pf == 'csv':
        response = HttpResponse(content_type='application/csv')
        response['Content-Disposition'] = 'filename="invs.csv"'
        response.write(gen_csv_from_generators(invs))
    elif pf == 'thermal':
        pdf = gen_pdf(invs)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="tickets.pdf"'
        response.write(pdf)
    elif pf == 'A4':
        pdf = gen_pdf(invs)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="tickets.pdf"'
        response.write(pdf)
    else:
        raise "Ticket format not found"
    return response

def get_sold_invs(session):
    from .models import InvitationType
    from .models import Invitation
    types = InvitationType.objects.filter(sessions__in=[session])
    types = types.filter(is_pass=False)
    return Invitation.objects.filter(type__in=types).count()

