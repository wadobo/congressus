# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='surname',
        ),
        migrations.AddField(
            model_name='ticket',
            name='address',
            field=models.TextField(verbose_name='address', default='XXX'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='arrival',
            field=models.DateField(verbose_name='Arrival date', default=datetime.datetime(2015, 10, 27, 10, 50, 17, 310515, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='comments',
            field=models.TextField(blank=True, null=True, verbose_name='Especial needs'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='departure',
            field=models.DateField(verbose_name='Departure date', default=datetime.datetime(2015, 10, 27, 10, 50, 20, 438713, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='food',
            field=models.CharField(choices=[('all', 'All'), ('vegetarian', 'Vegetarian'), ('vegan', 'Vegan')], default='all', verbose_name='food preferences', max_length=20),
        ),
        migrations.AddField(
            model_name='ticket',
            name='photo',
            field=models.ImageField(upload_to='photos', blank=True, null=True, verbose_name='photo'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='type',
            field=models.CharField(choices=[('sponsor', 'Sponsor'), ('regular', 'Regular'), ('student', 'Student')], default='regular', verbose_name='type', max_length=20),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='name',
            field=models.CharField(verbose_name='full name', max_length=200),
        ),
    ]
