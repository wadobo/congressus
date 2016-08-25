import os
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.utils import formats
from django.utils import timezone
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.platypus import *
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.lib import utils
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
from PyPDF2 import PdfFileMerger

from events.models import TicketTemplate
from events.models import SeatLayout


def short_hour(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return formats.date_format(dt, 'H:i')


class QRFlowable(Flowable):
    def __init__(self, qr_value):
        # init and store rendering value
        Flowable.__init__(self)
        self.qr_value = qr_value

    def wrap(self, availWidth, availHeight):
        # optionnal, here I ask for the biggest square available
        self.width = self.height = min(availWidth, availHeight)
        return self.width, self.height

    def draw(self):
        # here standard and documented QrCodeWidget usage on
        # Flowable canva
        qr_code = QrCodeWidget(self.qr_value)
        bounds = qr_code.getBounds()
        qr_width = (bounds[2] - bounds[0])
        qr_height = (bounds[3] - bounds[1])
        w = float(self.width)
        d = Drawing(w, w, transform=[w/qr_width, 0, 0, w/qr_height, 0, 0])
        d.add(qr_code)
        renderPDF.draw(d, self.canv, 0, 0)


def get_image(path, width=3*cm):
    path = path.encode('utf8')
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))


def generate_pdf(ticket, logo='img/logo.png', asbuf=False, inv=False):
    """ Generate ticket in pdf with the get ticket. """

    seatinfo = ''
    if inv:
        if ticket.type.is_pass:
            initials = "PAS"
        else:
            initials = "INV"
        price = _('%4.2f €') % ticket.get_price()
        tax = ticket.get_tax()
        template = TicketTemplate.objects.last()
        wcode = 'GEN' + str(ticket.generator.id)
        text = ticket.type.name
        if ticket.type.start and ticket.type.end:
            date = _('%(date)s (%(start)s to %(end)s)') % {
                'date': formats.date_format(ticket.type.start, "l d/m/Y"),
                'start': short_hour(ticket.type.start),
                'end': short_hour(ticket.type.end),
            }
        else:
            date = ''
    else:
        space = ticket.session.space.name
        session = ticket.session.name
        start = formats.date_format(ticket.session.start, "l d/m/Y")
        date = _('%(date)s (%(start)s to %(end)s)') % {
            'date': start,
            'start': short_hour(ticket.session.start),
            'end': short_hour(ticket.session.end),
        }
        wcode = ticket.window_code()
        initials = _('T') + space[0].upper() + session[0].upper()
        text = _('Ticket %(space)s %(session)s') % {'space': space.capitalize(), 'session': session.capitalize()}


        price = _('%4.2f €') % ticket.price
        tax = ticket.tax
        seatinfo = ''
        if ticket.seat:
            seatdata = {
                'layout': ticket.seat_layout.name,
                'row': ticket.seat_row(),
                'col': ticket.seat_column()
            }
            seatinfo = _('SECTOR: %(layout)s &nbsp;&nbsp;&nbsp; ROW: %(row)s &nbsp;&nbsp;&nbsp; SEAT: %(col)s') % seatdata
            seatinfo = '<font size=11><b>'+ seatinfo +'</b></font><br/>'
        template = ticket.session.template

    taxtext = _('TAX INC.')
    price = '<font size=14>%s</font>   <font size=8>%s%% %s</font>' % (price, tax, taxtext)
    code = ticket.order
    if settings.QRCODE:
        codeimg = QRFlowable(code)
    else:
        codeimg = code128.Code128(code, barWidth= 0.01 * inch, barHeight= .5 * inch)

    PAGE_HEIGHT= 11 * inch
    PAGE_WIDTH= 8.5 * inch
    styles = getSampleStyleSheet()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    doc.topMargin = 3.1*cm
    Story = []
    styleN = styles["Normal"]
    styleH = styles['Heading1']

    styleR = ParagraphStyle(name="rightStyle", fontSize=8, alignment=TA_RIGHT)
    styleL = ParagraphStyle(name="leftStyle", fontSize=8, alignment=TA_LEFT)
    styleLinks = ParagraphStyle(name="links", fontSize=14,
                                alignment=TA_CENTER, textColor=colors.gray)
    styleInfo = ParagraphStyle(name="info", alignment=TA_JUSTIFY, fontSize=7,
                               textColor=colors.gray)

    def add_full_width_image(header, img):
        pstyle = ParagraphStyle(name="leftStyle", fontSize=8,
                                alignment=TA_LEFT, textColor=colors.gray)
        Story.append(Spacer(width=1, height=8))
        Story.append(Paragraph(header, pstyle))
        Story.append(HRFlowable(width="100%", thickness=1, hAlign='CENTER',
                                vAlign='BOTTOM', dash=None, spaceAfter=5))
        img = get_image(img, width=doc.width - 8)
        Story.append(img)

    def ticketPage(canvas, doc):
        if logo and not template:
            img = get_image(os.path.join(settings.MEDIA_ROOT, logo), width=2*cm)
            canvas.saveState()
            img.drawOn(canvas, doc.width, doc.height + doc.topMargin)
            canvas.restoreState()
        elif template:
            header = template.header
            header = get_image(header.path, width=doc.width)

            canvas.saveState()
            header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 1*cm)
            canvas.restoreState()

        # drawing the footer
        canvas.saveState()

        # qrcode
        codeimg.wrap(3*cm, 3*cm)
        codeimg.drawOn(canvas, doc.width, 1.5*cm)
        # ticket window code
        pr = Paragraph(wcode, styleL)
        pr.wrap(doc.width, 1*cm)
        pr.drawOn(canvas, doc.leftMargin, 1.5*cm)
        # line
        hr = HRFlowable(width="100%", thickness=0.25, hAlign='CENTER',
                        color=colors.black, vAlign='BOTTOM', dash=None,
                        spaceAfter=5)
        hr.wrap(doc.width, 1*cm)
        hr.drawOn(canvas, doc.leftMargin, 1.5*cm)
        # code
        pr = Paragraph(code, styleL)
        pr.wrap(doc.width, 1*cm)
        pr.drawOn(canvas, doc.leftMargin, 1.0*cm)

        canvas.restoreState()

    # heading notice
    t = Table([
        [Paragraph(_("PRINT AND BRING THIS TICKET WITH YOU"), styleL),
         Paragraph("PRINT AND BRING THIS TICKET WITH YOU", styleR)]
    ], colWidths='*')
    tstyle_list = [ ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ]
    tstyle = TableStyle(tstyle_list)
    t.setStyle(tstyle)
    Story.append(t)

    # ticket information table
    t = Table([
        [codeimg, Paragraph('<font size=60>'+initials+'</font>', styleN), Paragraph(price, styleN)],
        ['',      Paragraph(text, styleN), ''],
        ['',      Paragraph(date, styleN), ''],
        ['',      Paragraph(seatinfo, styleN), ''],
        [code, '']
    ], colWidths=[5*cm, '*', 2.5*cm], rowHeights=[2.5*cm, 0.5*cm, 0.5*cm, 0.5*cm, 0.5*cm])
    tstyle_list = [
        ('VALIGN', (0,0), (0, 1), 'MIDDLE'),
        ('VALIGN', (0,0), (1,-1), 'TOP'),
        ('VALIGN', (-1,0), (-1,0), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('SPAN', (0, 0), (0, 3)),
    ]
    tstyle = TableStyle(tstyle_list)
    t.setStyle(tstyle)
    Story.append(t)

    if template:
        # sponsors
        if template.sponsors:
            add_full_width_image(_("Sponsors"), template.sponsors.path)

        # info text
        Story.append(Spacer(width=1, height=1*cm))

        t = Table([
            [Paragraph(template.links, styleLinks)],
            [Paragraph(template.info.replace('\n', '<br/>'), styleInfo)]
        ], colWidths=['*'], rowHeights=[1*cm, None])
        tstyle_list = [
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]
        tstyle = TableStyle(tstyle_list)
        t.setStyle(tstyle)
        Story.append(t)

        Story.append(Spacer(width=1, height=1*cm))

        # contributors
        if template.contributors:
            add_full_width_image(_("Contributors"), template.contributors.path)

    doc.build(Story, onFirstPage=ticketPage, onLaterPages=ticketPage)

    if not asbuf:
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    else:
        buffer.seek(0)
        return buffer

def concat_pdf(files):
    buffer = BytesIO()
    fm = PdfFileMerger()
    for f in files:
        fm.append(f)
    fm.write(buffer)
    fm.close()

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_ticket_format(mp, pf):
    """ With a list of invitations or invitations,generate ticket output """
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
    elif pf == 'thermal':
        pdf = mp.gen_pdf()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="tickets.pdf"'
        response.write(pdf)
    elif pf == 'A4':
        pdf = mp.gen_pdf()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="tickets.pdf"'
        response.write(pdf)
    else:
        raise "Ticket format not found"
    return response

def check_free_seats(sessions, res):
    # TODO: only look fisrt session
    session = sessions.first()
    for k in res.keys():
        layout = SeatLayout.objects.get(name=k)
        for v in res.get(k)[:]:
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
    res = check_free_seats(sessions, res)
    return res
