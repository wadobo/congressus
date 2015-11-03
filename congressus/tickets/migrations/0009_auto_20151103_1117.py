# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0008_auto_20151101_1217'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvCode',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('code', models.CharField(null=True, verbose_name='code', blank=True, max_length=10)),
                ('used', models.BooleanField(verbose_name='used', default=False)),
                ('event', models.ForeignKey(related_name='codes', to='tickets.Event')),
            ],
        ),
        migrations.AddField(
            model_name='ticket',
            name='inv',
            field=models.OneToOneField(null=True, to='tickets.InvCode', blank=True),
        ),
    ]
