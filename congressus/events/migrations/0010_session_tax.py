# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-11 08:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0009_auto_20160429_1111'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='tax',
            field=models.IntegerField(default=21, verbose_name='ticket tax percentage'),
        ),
    ]
