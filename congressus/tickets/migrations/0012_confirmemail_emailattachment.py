# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0011_event_price_invited'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('subject', models.CharField(verbose_name='subject', max_length=300)),
                ('body', models.TextField(verbose_name='body')),
                ('event', models.OneToOneField(to='tickets.Event')),
            ],
        ),
        migrations.CreateModel(
            name='EmailAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('attach', models.FileField(upload_to='attachments', verbose_name='attach')),
                ('email', models.ForeignKey(to='tickets.ConfirmEmail')),
            ],
        ),
    ]
