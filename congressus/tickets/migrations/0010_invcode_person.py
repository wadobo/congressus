# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0009_auto_20151103_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='invcode',
            name='person',
            field=models.CharField(null=True, max_length=100, blank=True, verbose_name='for person'),
        ),
    ]
