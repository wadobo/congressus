# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-07 16:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('windows', '0002_auto_20160603_1139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticketwindow',
            name='users',
        ),
    ]
