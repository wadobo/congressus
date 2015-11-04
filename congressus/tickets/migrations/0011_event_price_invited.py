# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0010_invcode_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='price_invited',
            field=models.IntegerField(default=0, verbose_name='invited price'),
        ),
    ]
