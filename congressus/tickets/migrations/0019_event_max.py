# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0018_invcode_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='max',
            field=models.IntegerField(default=300, verbose_name='max tickets'),
        ),
    ]
