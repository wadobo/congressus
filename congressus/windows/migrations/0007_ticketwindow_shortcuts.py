# Generated by Django 2.0.6 on 2018-11-16 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('windows', '0006_ticketwindow_print_close_timeout'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketwindow',
            name='shortcuts',
            field=models.JSONField(default={"add": 145, "onoff": 42, "sub": 19}),
        ),
    ]
