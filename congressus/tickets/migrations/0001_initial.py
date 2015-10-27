# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=200)),
                ('start', models.DateTimeField(verbose_name='start date')),
                ('end', models.DateTimeField(verbose_name='end date')),
                ('price', models.IntegerField(default=25, verbose_name='ticket price')),
                ('info', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-start'],
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('order', models.CharField(verbose_name='order', unique=True, max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('confirmed_date', models.DateTimeField(blank=True, verbose_name='confirmed at', null=True)),
                ('confirmed', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('surname', models.CharField(max_length=200, verbose_name='surname')),
                ('org', models.CharField(max_length=200, verbose_name='organization')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('event', models.ForeignKey(related_name='tickets', to='tickets.Event')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
