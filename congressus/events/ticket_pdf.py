from __future__ import annotations
from io import BytesIO
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import formats
from django.utils import timezone
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.platypus import (
    Flowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.lib import utils
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

if TYPE_CHECKING:
    from events.models import TicketTemplate


# Styles reportlab
STYLE_NORMAL = ParagraphStyle(name='normal', fontSize=10, leading=12)
STYLE_RIGHT = ParagraphStyle(name='right', fontSize=8, alignment=TA_RIGHT)
STYLE_LEFT = ParagraphStyle(name='left', fontSize=8, alignment=TA_LEFT)
STYLE_CENTER = ParagraphStyle(name='center', fontSize=8, alignment=TA_CENTER)
STYLE_LINK = ParagraphStyle(name='link', fontSize=14, alignment=TA_CENTER, textColor=colors.gray)
STYLE_INFO = ParagraphStyle(name='info', alignment=TA_JUSTIFY, fontSize=7, textColor=colors.gray)
STYLE_PARAGRAPH = ParagraphStyle(name='paragraph', fontSize=8, textColor=colors.gray)


def short_hour(date_time):
    if timezone.is_aware(date_time):
        date_time = timezone.localtime(date_time)
    return formats.date_format(date_time, 'H:i')


class TTR(Flowable):  # TableTextRotate
    '''Rotates a tex in a table cell.'''
    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(-90)
        canvas.drawString(8, -1, self.text)


class QRFlowable(Flowable):
    def __init__(self, qr_value: str, border: int = 4):
        # init and store rendering value
        Flowable.__init__(self)
        self.qr_value = qr_value
        self.border = border
        print('BORDER', self.border)

    def wrap(self, availWidth, availHeight):  # noqa
        # optionnal, here I ask for the biggest square available
        self.width = self.height = min(availWidth, availHeight)
        return self.width, self.height

    def draw(self):
        # here standard and documented QrCodeWidget usage on
        # Flowable canva
        qr_code = QrCodeWidget(self.qr_value, barBorder=self.border)
        bounds = qr_code.getBounds()
        qr_width = (bounds[2] - bounds[0])
        qr_height = (bounds[3] - bounds[1])
        _weight = float(self.width)
        drawing = Drawing(
            _weight,
            _weight,
            transform=[_weight / qr_width, 0, 0, _weight / qr_height, 0, 0]
        )
        drawing.add(qr_code)
        renderPDF.draw(drawing, self.canv, 0, 0)


def get_image(path, width):
    path = path.encode('utf8')
    img = utils.ImageReader(path)
    img_width, img_height = img.getSize()
    aspect = img_height / float(img_width)
    return Image(path, width=width, height=(width * aspect))


class TicketPDF:
    def __init__(self, ticket, is_invitation=False):
        self.ticket = ticket
        self.code = ticket.order
        self.is_invitation = is_invitation
        self.story = []
        self.template: TicketTemplate = self._calc_template()

        if not self.template:
            raise Exception(_('Not found ticket template'))

        self._buffer = BytesIO()
        self.doc = SimpleDocTemplate(self._buffer, **self.template.config_in(cm))

    def _calc_template(self) -> TicketTemplate:
        if self.is_invitation:
            return self.ticket.type.template
        return self.ticket.session.template

    def generate(self, asbuf: bool = False):
        self._add_header_img()
        self._add_sponsors_img()
        self._add_previous_note()
        self._add_ticket_info()
        self._add_next_note()

        self.doc.build(self.story, onFirstPage=self._on_first_page)

        if asbuf:
            self._buffer.seek(0)
            return self._buffer

        pdf = self._buffer.getvalue()
        self._buffer.close()
        return pdf

    def _add_header_img(self) -> None:
        header = self.template.header
        if header:
            self.story.append(get_image(header.path, width=self.doc.width))
            self._add_spacer()

    def _add_spacer(self, width: int = 1, height: int = 8) -> None:
        self.story.append(Spacer(width=width, height=height))

    def _add_sponsors_img(self) -> None:
        sponsors = self.template.sponsors
        if sponsors:
            self.story.append(get_image(sponsors.path, width=self.doc.width))
            self._add_spacer()

    def _add_previous_note(self) -> None:
        previous_note = self.template.previous_note
        if previous_note:
            self.story.append(Paragraph(previous_note, STYLE_NORMAL))

    def _add_ticket_info(self) -> None:
        price = Paragraph(self.price, STYLE_NORMAL)

        if self.template.is_vertical:
            table = Table(
                [
                    [self.codeimg],
                    [self.code, self.wcode],
                    [self.initials],
                    [self.text],
                    [self.date],
                    [self.seatinfo],
                    [price],
                ],
                rowHeights=[None, None, 2.5 * cm, None, None, None, None],
            )
            table_style = TableStyle([
                ('SPAN', (0, 0), (1, 0)),
                ('SPAN', (0, 2), (1, 2)),
                ('SPAN', (0, 3), (1, 3)),
                ('SPAN', (0, 4), (1, 4)),
                ('SPAN', (0, 5), (1, 5)),
                ('SPAN', (0, 6), (1, 6)),
                ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
                ('VALIGN', (0, 2), (0, 2), 'TOP'),
                ('SIZE', (0, 2), (0, 2), 60),
                ('ALIGN', (0, 2), (0, 6), 'CENTER'),
            ])
        else:
            initials = Paragraph(f'<font size=60>{self.initials}</font>', STYLE_NORMAL)
            table = Table(
                [
                    [self.codeimg, TTR(self.code), initials, price, self.codeimg],
                    ['', '', Paragraph(self.text, STYLE_NORMAL), '', ''],
                    ['', '', Paragraph(self.date, STYLE_NORMAL), '', ''],
                    ['', '', Paragraph(self.seatinfo, STYLE_NORMAL), '', ''],
                    ['', '', '', '', self.wcode],
                ],
                colWidths=[5 * cm, 0.5 * cm, 5.5 * cm, 2.3 * cm, 5 * cm],
                rowHeights=[2.5 * cm, 0.5 * cm, 0.5 * cm, 0.5 * cm, 0.5 * cm]
            )
            table_style = TableStyle([
                ('VALIGN', (0, 0), (0, 1), 'MIDDLE'),
                ('VALIGN', (-1, 0), (-1, 1), 'MIDDLE'),
                ('VALIGN', (0, 0), (2, -1), 'TOP'),
                ('VALIGN', (-2, 0), (-2, 0), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (-1, 0), (-1, 1), 'CENTER'),
                ('ALIGN', (-1, -1), (-1, -1), 'CENTER'),
                ('SPAN', (1, 0), (1, -1)),
                ('SPAN', (0, 0), (0, 3)),
                ('SPAN', (2, 1), (3, 1)),
                ('SPAN', (2, 2), (3, 2)),
                ('SPAN', (2, 3), (3, 3)),
                ('SPAN', (-1, 0), (-1, 3)),
            ])

        table.setStyle(table_style)
        self.story.append(table)

    def _add_next_note(self) -> None:
        next_note = self.template.next_note
        links = self.template.links

        if links:
            self._add_spacer(height=1 * cm)

            table = Table(
                [
                    [Paragraph(links, STYLE_LINK)],
                    [Paragraph(next_note.replace('\n', '<br/>'), STYLE_INFO)]
                ],
                rowHeights=[1 * cm, None]
            )
            table_style = TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ])
            table.setStyle(table_style)
            self.story.append(table)

            self._add_spacer(height=1 * cm)

        if not links and next_note:
            self._add_spacer(height=0.5 * cm)
            self.story.append(Paragraph(next_note, STYLE_RIGHT))

    def _on_first_page(self, canvas, doc) -> None:
        canvas.saveState()

        footer = self.template.footer
        if footer:
            img = get_image(footer.path, width=doc.width)
            img.drawOn(canvas, doc.leftMargin, doc.bottomMargin)

        canvas.restoreState()

    @property
    def codeimg(self):
        if settings.QRCODE:
            return QRFlowable(self.code, border=(0 if self.template.is_vertical else 4))
        return code128.Code128(self.code, barWidth=0.01 * inch, barHeight=0.5 * inch)

    @property
    def initials(self):
        ticket = self.ticket

        if self.is_invitation and ticket.type.is_pass:
            return "PAS"

        if self.is_invitation:
            return "INV"

        space = ticket.session.space.name
        session = ticket.session.name

        if ticket.session.short_name:
            return ticket.session.short_name
        return _('T') + space[0].upper() + session[0].upper()

    @property
    def text(self):
        if self.is_invitation and self.ticket.generator:
            return self.ticket.generator.concept

        if self.is_invitation:
            return self.ticket.type.name

        data = {
            'space': self.ticket.session.space.name.capitalize(),
            'session': self.ticket.session.name.capitalize()
        }
        return _('Ticket %(space)s %(session)s') % data

    @property
    def date(self):
        ticket = self.ticket

        if self.is_invitation:
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
        if self.is_invitation:
            strdate = dateformats['start']
        else:
            strdate = dateformats[ticket.session.dateformat]

        return strdate % {
            'date': start,
            'start': short_hour(sstart),
            'end': short_hour(send),
        }

    @property
    def wcode(self):
        ticket = self.ticket

        if self.is_invitation and ticket.generator:
            return 'GEN' + str(ticket.generator.id)

        if self.is_invitation:
            return 'INV'

        return ticket.window_code()

    @property
    def order(self):
        if self.is_invitation:
            return ''

        if self.ticket.mp:
            return self.ticket.mp.order_tpv or ''

        return self.ticket.order_tpv or ''

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
            seatinfo = f'<font size=11><b>{seatinfo}</b></font><br/>'
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
