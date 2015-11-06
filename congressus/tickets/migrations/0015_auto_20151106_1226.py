# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0014_auto_20151105_1054'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='address',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='photo',
        ),
    ]
