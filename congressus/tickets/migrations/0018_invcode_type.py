# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0017_auto_20151109_1235'),
    ]

    operations = [
        migrations.AddField(
            model_name='invcode',
            name='type',
            field=models.CharField(choices=[('invited', 'Invited'), ('speaker', 'Speaker'), ('student', 'Student')], max_length=15, default='invited', verbose_name='type'),
        ),
    ]
