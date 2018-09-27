import os
import random
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


def short_hour(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return formats.date_format(dt, 'H:i')


class TTR(Flowable): #TableTextRotate
    '''Rotates a tex in a table cell.'''
    def __init__(self, text):
        Flowable.__init__(self)
        self.text=text

    def draw(self):
        canvas = self.canv
        canvas.rotate(-90)
        canvas.drawString(8, -1, self.text)


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


def generate_thermal(ticket, asbuf=False, inv=False):
    pdf = TicketPDF(ticket, inv)
    return pdf.thermal(asbuf=asbuf)


def generate_pdf(ticket, asbuf=False, inv=False):
    pdf = TicketPDF(ticket, inv)
    return pdf.A4(asbuf=asbuf)


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


def get_ticket_format(mp, pf, attachment=True):
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
        pdf = mp.gen_thermal()
        response = HttpResponse(content_type='application/pdf')
        fname = 'filename="tickets.pdf"'
        if attachment:
            fname = 'attachment; ' + fname
        response['Content-Disposition'] = fname
        response.write(pdf)
    elif pf == 'A4':
        pdf = mp.gen_pdf()
        response = HttpResponse(content_type='application/pdf')
        fname = 'filename="tickets.pdf"'
        if attachment:
            fname = 'attachment; ' + fname
        response['Content-Disposition'] = fname
        response.write(pdf)
    else:
        raise "Ticket format not found"
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
    from events.models import SeatLayout
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


class TicketPDF:
    def __init__(self, ticket, inv=False):
        self.ticket = ticket
        self.code = ticket.order
        self.inv = inv

        self.story = []

        # reportlab common styles
        self.init_styles()

    def init_styles(self):
        styles = getSampleStyleSheet()
        self.styleN = styles["Normal"]
        self.styleH = styles['Heading1']
        self.styleR = ParagraphStyle(name="rightStyle", fontSize=8,
                            alignment=TA_RIGHT)
        self.styleL = ParagraphStyle(name="leftStyle", fontSize=8,
                            alignment=TA_LEFT)
        self.styleLinks = ParagraphStyle(name="links", fontSize=14,
                            alignment=TA_CENTER, textColor=colors.gray)
        self.styleInfo = ParagraphStyle(name="info",
                            alignment=TA_JUSTIFY, fontSize=7,
                            textColor=colors.gray)

        self.pstyle = ParagraphStyle(name="leftStyle", fontSize=8,
                            alignment=TA_LEFT, textColor=colors.gray)

    def A4_page_foot(self, canvas, doc):
        canvas.saveState()

        # qrcode
        qrcode = self.codeimg
        qrcode.wrap(3*cm, 3*cm)
        qrcode.drawOn(canvas, doc.width, 1.5*cm)
        # ticket order
        if self.order:
            pr = Paragraph(_('ORDER: %s') % self.order, self.styleL)
            pr.wrap(doc.width, 1*cm)
            pr.drawOn(canvas, doc.leftMargin, 1.5*cm)
        # line
        hr = HRFlowable(width="100%", thickness=0.25, hAlign='CENTER',
                        color=colors.black, vAlign='BOTTOM', dash=None,
                        spaceAfter=5)
        hr.wrap(doc.width, 1*cm)
        hr.drawOn(canvas, doc.leftMargin, 1.5*cm)
        # ticket window code
        pr = Paragraph(self.wcode, self.styleL)
        pr.wrap(doc.width, 1*cm)
        pr.drawOn(canvas, doc.leftMargin, 1.0*cm)
        # code
        pr = Paragraph(self.code, self.styleL)
        pr.wrap(doc.width, 1*cm)
        pr.drawOn(canvas, doc.width, 1.0*cm)

        canvas.restoreState()

    def A4_page(self, canvas, doc):
        if self.logo and not self.template:
            img = self.get_image(os.path.join(settings.MEDIA_ROOT, self.logo), width=2*cm)

            canvas.saveState()
            img.drawOn(canvas, doc.width, doc.height + doc.topMargin)
            canvas.restoreState()

        elif self.template and self.template.header:
            header = self.template.header
            header = self.get_image(header.path, width=doc.width)

            canvas.saveState()
            header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 1*cm)
            canvas.restoreState()

        # drawing the footer
        self.A4_page_foot(canvas, doc)

    def thermal_page(self, canvas, doc):
        if not self.thermal_template:
            return

        t = self.thermal_template

        canvas.saveState()

        if t.header:
            header = self.get_image(t.header.path, width=doc.width)
            header.drawOn(canvas, 0, doc.height - header._height)
        if t.sponsors:
            foot = self.get_image(t.sponsors.path, width=doc.width)
            foot.drawOn(canvas, 0, 0)
        if t.background:
            bg = self.get_image(t.background.path, width=doc.width)
            bg.drawOn(canvas, 0, 0)

        canvas.restoreState()

    def thermal_ticket_info(self):
        initials = Paragraph('<font size=60>'+ self.initials +'</font>', self.styleN)
        price = Paragraph(self.price, self.styleN)
        t = Table([
            [self.codeimg, TTR(self.code), initials, price, self.codeimg],
            ['', '', Paragraph(self.text, self.styleN), '', ''],
            ['', '', Paragraph(self.date, self.styleN), '', ''],
            ['', '', Paragraph(self.seatinfo, self.styleN), '', ''],
            ['', '', '', '', self.wcode],
        ], colWidths=[5*cm, 0.5*cm, 5.5*cm, 2.3*cm, 5*cm],
           rowHeights=[2.5*cm, 0.5*cm, 0.5*cm, 0.5*cm, 0.5*cm])
        tstyle_list = [
            ('VALIGN', (0,0), (0, 1), 'MIDDLE'),
            ('VALIGN', (-1,0), (-1, 1), 'MIDDLE'),
            ('VALIGN', (0,0), (2,-1), 'TOP'),
            ('VALIGN', (-2,0), (-2,0), 'TOP'),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (-1,0), (-1, 1), 'CENTER'),
            ('ALIGN', (-1,-1), (-1, -1), 'CENTER'),
            ('SPAN', (1, 0), (1, -1)),
            ('SPAN', (0, 0), (0, 3)),
            ('SPAN', (2, 1), (3, 1)),
            ('SPAN', (2, 2), (3, 2)),
            ('SPAN', (2, 3), (3, 3)),
            ('SPAN', (-1, 0), (-1, 3)),
            # DEBUG: preview grid
            #('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ]
        tstyle = TableStyle(tstyle_list)
        t.setStyle(tstyle)
        self.story.append(t)

    def ticket_info(self):
        initials = Paragraph('<font size=60>'+ self.initials +'</font>', self.styleN)
        price = Paragraph(self.price, self.styleN)
        t = Table([
            [self.codeimg, initials, price],
            ['', Paragraph(self.text, self.styleN), ''],
            ['', Paragraph(self.date, self.styleN), ''],
            ['', Paragraph(self.seatinfo, self.styleN), ''],
            [self.code, '']
        ], colWidths=[5*cm, '*', 2.5*cm],
           rowHeights=[2.5*cm, 0.5*cm, 0.5*cm, 0.5*cm, 0.5*cm])
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
        self.story.append(t)

    def heading_notice(self):
        t = Table([
            [Paragraph(_("PRINT AND BRING THIS TICKET WITH YOU"), self.styleL),
             Paragraph("PRINT AND BRING THIS TICKET WITH YOU", self.styleR)]
        ], colWidths='*')
        tstyle_list = [ ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ]
        tstyle = TableStyle(tstyle_list)
        t.setStyle(tstyle)
        self.story.append(t)


    def note(self):
        if not self.template or not self.template.note:
            return

        self.story.append(Paragraph('<font size=6><b>' + self.template.note + '</b></font>', self.styleR))

    def sponsors(self):
        if not self.template or not self.template.sponsors:
            return
        self.add_full_width_image(_("Sponsors"), self.template.sponsors.path)

    def infotext(self):
        if not self.template or not self.template.info:
            return
        self.story.append(Spacer(width=1, height=1*cm))

        t = Table([
            [Paragraph(self.template.links, self.styleLinks)],
            [Paragraph(self.template.info.replace('\n', '<br/>'), self.styleInfo)]
        ], colWidths=['*'], rowHeights=[1*cm, None])
        tstyle_list = [
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]
        tstyle = TableStyle(tstyle_list)
        t.setStyle(tstyle)
        self.story.append(t)

        self.story.append(Spacer(width=1, height=1*cm))

    def contributors(self):
        if not self.template or not self.template.contributors:
            return
        self.add_full_width_image(_("Contributors"), self.template.contributors.path)


    def A4(self, asbuf=False):
        self.logo='img/logo.png'

        buffer = BytesIO()
        self.doc = SimpleDocTemplate(buffer)
        self.doc.topMargin = 3.1*cm

        self.heading_notice()
        self.ticket_info()
        self.note()
        self.sponsors()
        self.infotext()
        self.contributors()

        self.doc.build(self.story, onFirstPage=self.A4_page,
                                   onLaterPages=self.A4_page)

        if not asbuf:
            pdf = buffer.getvalue()
            buffer.close()
            return pdf
        else:
            buffer.seek(0)
            return buffer

    def thermal(self, asbuf=False):
        buffer = BytesIO()
        w = 500
        h = 815 * w / 1795
        self.pagesize = (w, h)

        if self.thermal_template:
            self.pagesize = (self.thermal_template.width,
                             self.thermal_template.height)

        self.doc = SimpleDocTemplate(buffer,
                            pagesize=self.pagesize, topMargin=0,
                            leftMargin=0, bottomMargin=0,
                            rightMargin=0)

        self.story.append(Spacer(width=1, height=50))
        self.thermal_ticket_info()

        self.doc.build(self.story, onFirstPage=self.thermal_page,
                                   onLaterPages=self.thermal_page)

        if not asbuf:
            pdf = buffer.getvalue()
            buffer.close()
            return pdf
        else:
            buffer.seek(0)
            return buffer

    def add_full_width_image(self, header, img):
        self.story.append(Spacer(width=1, height=8))
        self.story.append(Paragraph(header, self.pstyle))
        self.story.append(HRFlowable(width="100%", thickness=1,
                                     hAlign='CENTER', vAlign='BOTTOM',
                                     dash=None, spaceAfter=5))
        img = self.get_image(img, width=self.doc.width - 8)
        self.story.append(img)

    def get_image(self, path, width=3*cm):
        path = path.encode('utf8')
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        return Image(path, width=width, height=(width * aspect))

    @property
    def codeimg(self):
        if settings.QRCODE:
            codeimg = QRFlowable(self.code)
        else:
            codeimg = code128.Code128(self.code, barWidth= 0.01 * inch, barHeight= .5 * inch)

        return codeimg

    @property
    def initials(self):
        ticket = self.ticket

        if self.inv:
            if ticket.type.is_pass:
                return "PAS"
            else:
                return "INV"

        space = ticket.session.space.name
        session = ticket.session.name

        if ticket.session.short_name:
            initials = ticket.session.short_name
        else:
            initials = _('T') + space[0].upper() + session[0].upper()
        return initials

    @property
    def text(self):
        if self.inv:
            if self.ticket.generator:
                return self.ticket.generator.concept
            return self.ticket.type.name

        space = self.ticket.session.space.name
        session = self.ticket.session.name
        text = _('Ticket %(space)s %(session)s') % {'space': space.capitalize(), 'session': session.capitalize()}
        return text

    @property
    def date(self):
        ticket = self.ticket

        if self.inv:
            sstart = ticket.type.start
            send = ticket.type.end

            if not sstart or not send:
                return ''
        else:
            sstart = ticket.session.start
            send = ticket.session.end

        start = formats.date_format(sstart, "l d/m/Y")

        dateformats = {
            'start': _('%(date)s (%(start)s)'),
            'complete': _('%(date)s (%(start)s to %(end)s)'),
            'onlydate': _('%(date)s'),
        }
        if self.inv:
            strdate = dateformats['start']
        else:
            strdate = dateformats[ticket.session.dateformat]

        date = strdate % {
            'date': start,
            'start': short_hour(sstart),
            'end': short_hour(send),
        }

        return date

    @property
    def wcode(self):
        ticket = self.ticket

        if self.inv:
            if ticket.generator:
                return 'GEN' + str(ticket.generator.id)
            else:
                return 'INV'

        wcode = ticket.window_code()
        return wcode

    @property
    def order(self):
        if self.inv:
            return ''

        if self.ticket.mp:
            order = self.ticket.mp.order_tpv or ''
        else:
            order = self.ticket.order_tpv or ''

        return order

    @property
    def seatinfo(self):
        ticket = self.ticket
        seatinfo = ''
        if ticket.seat:
            seatdata = {
                'layout': ticket.seat_layout.name,
                'row': ticket.seat_row(),
                'col': ticket.seat_column()
            }
            seatinfo = _('SECTOR: %(layout)s ROW: %(row)s SEAT: %(col)s') % seatdata
            seatinfo = '<font size=11><b>'+ seatinfo +'</b></font><br/>'
        return seatinfo

    @property
    def price(self):
        ticket = self.ticket

        if ticket.sold_in_window:
            price = ticket.get_window_price()
        else:
            price = ticket.get_price()
        if not price:
            return ''

        price = _('%4.2f €') % price
        tax = ticket.get_tax()

        taxtext = _('TAX INC.')
        price = '<font size=14>%s</font>   <font size=8>%s%% %s</font>' % (price, tax, taxtext)
        return price

    @property
    def template(self):
        if self.inv:
            return self.ticket.type.template
        return self.ticket.session.template

    @property
    def thermal_template(self):
        if self.inv:
            return self.ticket.type.thermal_template
        return self.ticket.session.thermal_template


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
