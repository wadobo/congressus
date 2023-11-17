# Generated by Django 4.2.5 on 2023-10-31 11:57

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0018_alter_tickettemplate_extra_html_and_more'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='session',
            managers=[
                ('read_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='tickettemplate',
            name='extra_html',
            field=models.TextField(default='\n<div class="page">\n  {% if template.header %}\n    <div class="header">\n      <img src={{ template.header.url }} />\n    </div>\n  {% endif %}\n\n  {% if template.sponsors %}\n    <div class="sponsors">\n      <img src={{ template.sponsors.url }} />\n    </div>\n  {% endif %}\n\n  <div class="note">\n    {{ template.previous_note }}\n  </div>\n\n  <div class="text">\n    {{ ticket.text }}\n  </div>\n\n  <div class="date">\n    {{ ticket.date }}\n  </div>\n\n  <div class="total_price">\n    {{ ticket.total_price|safe }}\n  </div>\n\n  <div class="initials">\n    {{ ticket.initials }}\n  </div>\n\n  <div class="seatinfo">\n    {{ ticket.seatinfo }}\n  </div>\n\n  {% if ticket.seat_layout %}\n  <table class="seatinfo2">\n    <thead>\n      <tr>\n        {% if ticket.seat_layout.name %}\n          <th>SECTOR</th>\n        {% endif %}\n        {% if ticket.seat_row %}\n          <th>ROW</th>\n        {% endif %}\n        {% if ticket.seat_column %}\n          <th>SEAT</th>\n        {% endif %}\n      </tr>\n    </thead>\n    <tbody>\n      <tr>\n        {% if ticket.seat_layout.name %}\n          <td>{{ ticket.seat_layout.name }}</td>\n        {% endif %}\n        {% if ticket.seat_row %}\n          <td>{{ ticket.seat_row }}</td>\n        {% endif %}\n        {% if ticket.seat_column %}\n          <td>{{ ticket.seat_column }}</td>\n        {% endif %}\n      </tr>\n    </tbody>\n  </table>\n  {% endif %}\n\n  <div class="codeimg">\n    <img src="data:image/png;base64,{{ qr_group }}" />\n    <div class="order">\n      {{ ticket.mp.order }}\n    </div>\n  </div>\n\n  <div class="codeimg">\n    <img src="data:image/png;base64,{{ qr }}" />\n    <div class="order">\n      {{ ticket.order }}\n    </div>\n  </div>\n\n  <div class="wcode">\n    {{ ticket.wcode }}\n  </div>\n\n  <div class="next_note">\n    {{ template.next_note }}\n  </div>\n\n  <div class="links">\n    {{ template.links }}\n  </div>\n\n  {% if template.footer %}\n    <div class="footer">\n      <img src={{ template.footer.url }} />\n    </div>\n  {% endif %}\n</div>\n', help_text='Extra html for configure template', verbose_name='extra html'),
        ),
        migrations.AlterField(
            model_name='tickettemplate',
            name='extra_style',
            field=models.TextField(blank=True, default='\nimg {\n  width: 100%;\n}\n\n.header, .sponsors, .footer {\n  display: block;\n  width: 100%;\n}\n\n.note, .text, .date, .next_note, .links {\n  display: block;\n}\n\n.price {\n  font-size: large;\n}\n\n.tax {\n  display: block;\n  font-size: small;\n}\n\n.initials {\n  display: block;\n  text-align: center;\n  font-size: xxx-large;\n}\n\n.codeimg {\n  margin: auto;\n  display: block;\n  width: 70%;\n}\n\n.order {\n  text-align: center;\n  margin-top: -2rem;\n}\n\n.seatinfo {\n  height: 100%;\n  display: none;\n  text-align: end;\n}\n\ntable .seatinfo2 {\n  height: 100%;\n  display: block;\n}\n\ntable td {\n  text-align: center;\n}\n\n.wcode {\n  display: block;\n  text-align: end;\n  font-size: small;\n}\n', help_text='Extra style in css for configure template', null=True, verbose_name='extra style'),
        ),
    ]
