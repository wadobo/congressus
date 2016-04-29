import os
from django.conf import settings
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import *
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128


def generate_pdf(ticket, logo='img/logo.png'):
    """ Generate ticket in pdf with the get ticket. """

    data = {
        'title': ticket.seesion.name,
        'date': ticket.seesion.start.isoformat(),
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

    def gen_ticket(filename):
        doc = SimpleDocTemplate(filename)
        Story = []
        styleN = styles["Normal"]
        styleH = styles['Heading1']
        Story.append(Paragraph(data.get('title'), styleH))
        Story.append(Spacer(1 * inch, .5 * inch))
        Story.append(Paragraph("Date: %s" % (data.get('date')), styleN))
        Story.append(Spacer(1 * inch, .25 * inch))
        Story.append(Paragraph("Code: %s" % (data.get('code')), styleN))
        Story.append(Spacer(1 * inch, .5 * inch))
        barcode=code128.Code128(data.get('code'), barWidth= 0.01 * inch, barHeight= .5 * inch)
        Story.append(barcode)
        doc.build(Story, onFirstPage=ticketPage, onLaterPages=ticketPage)
        return

    fname =  data.get('code') + ".pdf"
    f = os.path.join(settings.MEDIA_ROOT, 'tickets', fname)
    gen_ticket(f)
