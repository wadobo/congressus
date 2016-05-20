# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-13 07:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_session_tax'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeatLayout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='name')),
                ('top', models.IntegerField(default=0)),
                ('left', models.IntegerField(default=0)),
                ('direction', models.CharField(choices=[('t', 'Top'), ('l', 'Left'), ('r', 'Right'), ('d', 'Down')], default='d', max_length=2)),
                ('layout', models.TextField(help_text='the layout to select the numbered seat', verbose_name='seats layout')),
            ],
        ),
        migrations.CreateModel(
            name='SeatMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='name')),
                ('img', models.ImageField(blank=True, null=True, upload_to='maps', verbose_name='map image')),
            ],
        ),
        migrations.RemoveField(
            model_name='space',
            name='layout',
        ),
        migrations.AddField(
            model_name='seatlayout',
            name='map',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='layouts', to='events.SeatMap'),
        ),
        migrations.AddField(
            model_name='space',
            name='seat_map',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='spaces', to='events.SeatMap'),
        ),
    ]