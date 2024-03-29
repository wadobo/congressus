# Generated by Django 4.2.2 on 2023-09-04 15:49

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0012_tickettemplate_extra_html_alter_event_slug_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='space',
            name='description',
            field=tinymce.models.HTMLField(blank=True, default='', help_text='Igual que el campo título, aunque como el css lo añadimos nosotros, la clase la tendremos que crear nosotros.', verbose_name='description'),
        ),
        migrations.AddField(
            model_name='space',
            name='foot_description',
            field=tinymce.models.HTMLField(blank=True, default='', help_text='Igual que la descripción', verbose_name='foot description'),
        ),
        migrations.AddField(
            model_name='space',
            name='is_folding',
            field=models.BooleanField(default=False, help_text='El espacio será mostrado utilizando un details summary en html, por defecto estará desplegado, si queremos que por defecto aparezca plegado, tendremos que activar esta opción.', verbose_name='is folding'),
        ),
        migrations.AddField(
            model_name='space',
            name='title',
            field=tinymce.models.HTMLField(default='', help_text="Por defecto, el título se mostrará sin estilos, si queremos aplicar algún estilo al título, tendremos que hacerlo desde el panel de administración, en theme --> theme config --> custom css, usando la class 'title'", verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='tickettemplate',
            name='extra_style',
            field=models.TextField(blank=True, default='\n.header {\n  grid-area: header;\n  width: 100%;\n}\n\nimg {\n  width: 100%;\n}\n\n.sponsors {\n  grid-area: sponsors;\n}\n\n.note {\n  grid-area: note;\n}\n\n.total_price {\n  grid-area: total_price;\n}\n\n.price {\n  font-size: large;\n}\n\n.tax {\n  font-size: small;\n}\n\n.codeimg {\n  margin: auto;\n  grid-area: codeimg;\n}\n\n.order {\n  grid-area: order;\n}\n\n.wcode {\n  grid-area: wcode;\n  text-align: end;\n}\n\n.initials {\n  grid-area: initials;\n  text-align: center;\n  font-size: xxx-large;\n}\n\n.text {\n  grid-area: text;\n  text-align: center;\n}\n\n.date {\n  grid-area: date;\n  text-align: center;\n}\n\n.seatinfo {\n  height: 100%;\n  grid-area: seatinfo;\n  text-align: end;\n}\n\n.seatinfo2 {\n  height: 100%;\n  grid-area: seatinfo2;\n  display: none;\n}\n\n.seatinfo_sector {\n  height: 100%;\n  grid-area: seatinfo_sector;\n  display: none;\n}\n\n.seatinfo_row {\n  height: 100%;\n  grid-area: seatinfo_row;\n  display: none;\n}\n\n.seatinfo_seat {\n  height: 100%;\n  grid-area: seatinfo_seat;\n  display: none;\n}\n\n.next_note {\n  grid-area: next_note;\n}\n\n.footer {\n  grid-area: footer;\n  width: 100%;\n}\n', help_text='Extra style in css for configure template', null=True, verbose_name='extra style'),
        ),
    ]
