# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-02 09:44
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0225_WARNING_INDEX_20180129_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningunityear',
            name='credits',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(500)]),
        ),
    ]