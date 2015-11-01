# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_auto_20151028_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='order_tpv',
            field=models.CharField(blank=True, null=True, max_length=12, verbose_name='order TPV'),
        ),
    ]
