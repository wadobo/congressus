# Generated by Django 2.0.13 on 2019-11-23 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('windows', '0008_ticketwindow_autocall_singlerow'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketwindow',
            name='number_of_calls',
            field=models.PositiveSmallIntegerField(default=1, help_text='Number of calls created to singlerow when open ticket windows', verbose_name='number of call'),
        ),
    ]
