# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0012_confirmemail_emailattachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmemail',
            name='event',
            field=models.OneToOneField(to='tickets.Event', related_name='email'),
        ),
    ]
