# Generated by Django 4.2.2 on 2023-09-09 19:46

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='multipurchase',
            managers=[
                ('read_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
