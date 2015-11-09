# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0015_auto_20151106_1226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='comments',
            field=models.TextField(null=True, verbose_name='Special needs', blank=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='confirmed_date',
            field=models.DateTimeField(null=True, verbose_name='Confirmed at', blank=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='food',
            field=models.CharField(default='all', choices=[('all', 'All'), ('vegetarian', 'Vegetarian'), ('vegan', 'Vegan')], verbose_name='Food preferences', max_length=20),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Full name'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='order',
            field=models.CharField(max_length=200, verbose_name='Order', unique=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='order_tpv',
            field=models.CharField(max_length=12, null=True, verbose_name='Order TPV', blank=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='org',
            field=models.CharField(max_length=200, verbose_name='Organization'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='type',
            field=models.CharField(default='regular', choices=[('invited', 'Invited'), ('speaker', 'Speaker'), ('sponsor', 'Sponsor'), ('regular', 'Regular'), ('student', 'Student')], verbose_name='Type', max_length=20),
        ),
    ]
