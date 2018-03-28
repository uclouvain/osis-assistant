# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-28 06:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0249_merge_20180327_1439'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learningunityear',
            name='summary_editable',
        ),
        migrations.AddField(
            model_name='learningunityear',
            name='summary_locked',
            field=models.BooleanField(default=False, verbose_name='summary_locked'),
        ),
    ]
