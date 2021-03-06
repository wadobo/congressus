# Generated by Django 2.0.6 on 2018-10-16 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20180718_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketfield',
            name='show_in_tws',
            field=models.BooleanField(default=False, help_text='Only can show one field per event. If you check this field, other field could be unchecked', verbose_name='show in ticket window sale'),
        ),
    ]
