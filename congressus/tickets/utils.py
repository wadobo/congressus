import os
from django.conf import settings
from django.utils.translation import ugettext as _
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


def generate_pdf(ticket, logo='img/logo.png', asbuf=False):
    """ Generate ticket in pdf with the get ticket. """

    space = ticket.session.space.name
    session = ticket.session.name
    start = ticket.session.start.strftime("%A %d/%m/%Y")
    date = _('%s (%s to %s)') % (
        start,
        ticket.session.start.strftime("%H:%M"), 
        ticket.session.end.strftime("%H:%M")
    )
    code = ticket.order

    initials = _('T') + space[0].upper() + session[0].upper()
    text = _('Ticket %(space)s %(session)s') % {'space': space.capitalize(), 'session': session.capitalize()}
    if ticket.seat:
        text += ' ' + ticket.cseat()

    price = _('%4.2f €') % ticket.price
    price = '<font size=14>%s</font>   <font size=8>%s%% TAX INC.</font>' % (price, ticket.tax)

    if settings.QRCODE:
        codeimg = QRFlowable(code)
    else:
        codeimg = code128.Code128(code, barWidth= 0.01 * inch, barHeight= .5 * inch)

    PAGE_HEIGHT= 11 * inch
    PAGE_WIDTH= 8.5 * inch
    styles = getSampleStyleSheet()

    template = ticket.session.template

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    Story = []
    styleN = styles["Normal"]
    styleH = styles['Heading1']

    styleR = ParagraphStyle(name="rightStyle", fontSize=8, alignment=TA_RIGHT)
    styleL = ParagraphStyle(name="leftStyle", fontSize=8, alignment=TA_LEFT)
    styleLinks = ParagraphStyle(name="links", fontSize=14,
                                alignment=TA_CENTER, textColor=colors.gray)
    styleInfo = ParagraphStyle(name="info", alignment=TA_JUSTIFY)

    def add_full_width_image(header, img):
        Story.append(Spacer(width=1, height=8))
        Story.append(Paragraph(header, styleL))
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
            header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin)
            canvas.restoreState()

        # drawing the footer
        canvas.saveState()

        # qrcode
        codeimg.wrap(3*cm, 3*cm)
        codeimg.drawOn(canvas, doc.width, 1.5*cm)
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
        [codeimg, Paragraph('<font size=60>'+initials+'</font>', styleN)],
        ['',      Paragraph(text, styleN)],
        ['',      Paragraph(date, styleN)],
        ['',      Paragraph(price, styleN)],
        [code, '']
    ], colWidths=[5*cm, '*'], rowHeights=[2.5*cm, 0.5*cm, 0.5*cm, 0.5*cm, 0.5*cm])
    tstyle_list = [
        ('VALIGN', (0,0), (1,-1), 'TOP'),
        ('VALIGN', (0,0), (0,-1), 'MIDDLE'),
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
