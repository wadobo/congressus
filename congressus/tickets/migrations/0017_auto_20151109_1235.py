# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0016_auto_20151109_1127'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='price_sponsor',
        ),
        migrations.AlterField(
            model_name='ticket',
            name='type',
            field=models.CharField(default='regular', choices=[('invited', 'Invited'), ('speaker', 'Speaker'), ('regular', 'Regular'), ('student', 'Student')], max_length=20, verbose_name='Type'),
        ),
    ]
