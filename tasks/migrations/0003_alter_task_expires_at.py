# Generated by Django 4.1.2 on 2022-11-22 20:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='expires_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 11, 29, 23, 14, 7, 402713)),
        ),
    ]
