# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0007_ticket_confirm_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='type',
            field=models.CharField(choices=[('invited', 'Invited'), ('speaker', 'Speaker'), ('sponsor', 'Sponsor'), ('regular', 'Regular'), ('student', 'Student')], verbose_name='type', default='regular', max_length=20),
        ),
    ]
