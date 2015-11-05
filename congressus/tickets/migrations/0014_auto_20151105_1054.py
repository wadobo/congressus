# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0013_auto_20151105_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailattachment',
            name='email',
            field=models.ForeignKey(to='tickets.ConfirmEmail', related_name='attachs'),
        ),
    ]
