# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-25 09:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invs', '0005_auto_20160825_0301'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitationgenerator',
            name='seats',
            field=models.CharField(blank=True, help_text='C1[1-1,1-3]; C2[2-1:2-4]', max_length=1024, null=True, verbose_name='seats'),
        ),
    ]
