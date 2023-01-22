# Generated by Django 4.1.2 on 2023-01-21 23:39

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_author_rating_normalized_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='author_rating_normalized',
            field=models.FloatField(default=7.5, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='user',
            name='implementer_rating_normalized',
            field=models.FloatField(default=7.5, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
