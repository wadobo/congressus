# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0004_event_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='price_speaker',
            field=models.IntegerField(verbose_name='speaker price', default=0),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='type',
            field=models.CharField(verbose_name='type', choices=[('speaker', 'Speaker'), ('sponsor', 'Sponsor'), ('regular', 'Regular'), ('student', 'Student')], max_length=20, default='regular'),
        ),
    ]
