# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_ticket_order_tpv'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='confirm_sent',
            field=models.BooleanField(default=False),
        ),
    ]
