# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-17 06:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('windows', '0004_auto_20160607_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketWindowCashMovement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('add', 'Add'), ('remove', 'Remove')], default='add', max_length=10)),
                ('amount', models.PositiveIntegerField(default=0)),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='ticketwindow',
            name='cash',
            field=models.IntegerField(default=0, verbose_name='cash in the ticket window'),
        ),
        migrations.AddField(
            model_name='ticketwindowcashmovement',
            name='window',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='windows.TicketWindow'),
        ),
    ]
