# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-11-03 13:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0073_auto_20161028_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='offeryear',
            name='enrollment_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
