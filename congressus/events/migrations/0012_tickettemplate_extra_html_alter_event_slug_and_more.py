# Generated by Django 4.2.2 on 2023-08-03 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0011_tickettemplate_is_html_format'),
    ]

    operations = [
        migrations.AddField(
            model_name='tickettemplate',
            name='extra_html',
            field=models.TextField(default='\n<div class="page">\n  {% if template.header %}\n    <div class="header">\n      <img src={{ template.header.url }} />\n    </div>\n  {% endif %}\n\n  {% if template.sponsors %}\n    <div class="sponsors">\n      <img src={{ template.sponsors.url }} />\n    </div>\n  {% endif %}\n\n  <div class="note">\n    {{ template.previous_note }}\n  </div>\n\n  <div class="total_price">\n    {{ ticket.total_price|safe }}\n  </div>\n\n  <div class="codeimg">\n    <img src="data:image/png;base64,{{ ticket.gen_qr }}" />\n  </div>\n\n  <div class="order">\n    {{ ticket.order }}\n  </div>\n\n  <div class="wcode">\n    {{ ticket.wcode }}\n  </div>\n\n  <div class="initials">\n    {{ ticket.initials }}\n  </div>\n\n  <div class="text">\n    {{ ticket.text }}\n  </div>\n\n  <div class="date">\n    {{ ticket.date }}\n  </div>\n\n  <div class="seatinfo">\n    {{ ticket.seatinfo }}\n  </div>\n\n  <div class="seatinfo2">\n    {% if ticket.seat_layout and ticket.seat_layout.name %}\n      <div class="seatinfo_sector">\n        {{ ticket.seat_layout.name }}\n      </div>\n    {% endif %}\n\n    {% if ticket.seat_row %}\n      <div class="seatinfo_row">\n        {{ ticket.seat_row }}\n      </div>\n    {% endif %}\n\n    {% if ticket.seat_column %}\n      <div class="seatinfo_seat">\n        {{ ticket.seat_column }}\n      </div>\n    {% endif %}\n  </div>\n\n  <div class="next_note">\n    {{ ticket.next_note }}\n  </div>\n\n  {% if template.footer %}\n    <div class="footer">\n      <img src={{ template.footer.url }} />\n    </div>\n  {% endif %}\n</div>\n', help_text='Extra html for configure template', verbose_name='extra html'),
        ),
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterField(
            model_name='session',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterField(
            model_name='space',
            name='slug',
            field=models.SlugField(),
        ),
    ]
