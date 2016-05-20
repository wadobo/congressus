import os
from django.conf import settings
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.platypus import *
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO


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
        qr_width = (bounds[2] - bounds[0])*2
        qr_height = (bounds[3] - bounds[1])*2
        w = float(self.width)
        d = Drawing(w, w, transform=[w/qr_width, 0, 0, w/qr_height, 0, 0])
        d.add(qr_code)
        renderPDF.draw(d, self.canv, 90, 230)


def generate_pdf(ticket, logo='img/logo.png'):
    """ Generate ticket in pdf with the get ticket. """

    data = {
        'title': ticket.session.name,
        'date': ticket.session.start.date().isoformat(),
        'code': ticket.order.upper(),
    }

    PAGE_HEIGHT= 11 * inch
    PAGE_WIDTH= 8.5 * inch
    styles = getSampleStyleSheet()

    def ticketPage(canvas, doc):
        if logo:
            canvas.saveState()
            H = 1.5 * inch
            W = 1.5 * .69 * inch
            canvas.drawImage(os.path.join(settings.MEDIA_ROOT, logo), 6 * inch,
                    PAGE_HEIGHT - (1.75 * inch), width = W, height = H)
            canvas.restoreState()

    def gen_ticket():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        Story = []
        styleN = styles["Normal"]
        styleH = styles['Heading1']
        Story.append(Paragraph(data.get('title'), styleH))
        Story.append(Spacer(1 * inch, .5 * inch))
        Story.append(Paragraph("Date: %s" % (data.get('date')), styleN))
        Story.append(Spacer(1 * inch, .25 * inch))
        Story.append(Paragraph("Code: %s" % (data.get('code')), styleN))
        Story.append(Spacer(1 * inch, .5 * inch))
        if settings.QRCODE:
            code = QRFlowable(data.get('code'))
        else:
            code = code128.Code128(data.get('code'), barWidth= 0.01 * inch, barHeight= .5 * inch)
        Story.append(code)
        doc.build(Story, onFirstPage=ticketPage, onLaterPages=ticketPage)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    return gen_ticket()
