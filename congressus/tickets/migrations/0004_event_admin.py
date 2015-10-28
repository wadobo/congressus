# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_auto_20151027_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='admin',
            field=models.EmailField(null=True, blank=True, verbose_name='admin email', max_length=254),
        ),
    ]
