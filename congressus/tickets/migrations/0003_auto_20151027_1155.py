# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_auto_20151027_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='price_sponsor',
            field=models.IntegerField(default=25, verbose_name='sponsor price'),
        ),
        migrations.AddField(
            model_name='event',
            name='price_student',
            field=models.IntegerField(default=25, verbose_name='student price'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='arrival',
            field=models.DateField(verbose_name='Arrival date', help_text='dd/mm/YYYY'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='departure',
            field=models.DateField(verbose_name='Departure date', help_text='dd/mm/YYYY'),
        ),
    ]
