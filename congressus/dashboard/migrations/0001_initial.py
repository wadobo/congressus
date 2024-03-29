# Generated by Django 2.0.6 on 2018-06-16 19:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigChart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('os_c', 'Online sales chart'), ('ws_c', 'Window sales chart'), ('a_c', 'Access chart'), ('os_p', 'Online sales pie'), ('ws_p', 'Window sales pie'), ('a_p', 'Access pie'), ('ws_b', 'Window sales bar')], default='os_c', max_length=8, verbose_name='type')),
                ('timestep', models.CharField(choices=[('daily', 'daily'), ('hourly', 'hourly'), ('minly', 'each minute')], default='daily', max_length=10, verbose_name='time step')),
                ('max_steps', models.IntegerField(default=10, verbose_name='maximum steps')),
            ],
        ),
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('num_cols', models.CharField(choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('6', '6')], default='2', max_length=2, verbose_name='number columns')),
                ('slug', models.SlugField(editable=False)),
                ('charts', models.ManyToManyField(to='dashboard.ConfigChart')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.Event', verbose_name='event')),
            ],
        ),
    ]
