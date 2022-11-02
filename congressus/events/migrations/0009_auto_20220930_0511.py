# Generated by Django 2.2.28 on 2022-09-30 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_tickettemplate_border_qr'),
    ]

    operations = [
        migrations.AddField(
            model_name='tickettemplate',
            name='extra_style',
            field=models.TextField(blank=True, help_text='Extra style in css for configure template', null=True, verbose_name='extra style'),
        ),
        migrations.AddField(
            model_name='tickettemplate',
            name='qr_size',
            field=models.FloatField(default=10, help_text='in cm', verbose_name='qr size'),
        ),
        migrations.AlterField(
            model_name='tickettemplate',
            name='border_qr',
            field=models.FloatField(default=4, verbose_name='border qr'),
        ),
    ]