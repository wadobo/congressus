# Generated by Django 4.2.2 on 2023-09-12 11:06

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0016_alter_session_window_template'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='event',
            managers=[
                ('read_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.RemoveField(
            model_name='tickettemplate',
            name='is_html_format',
        ),
    ]