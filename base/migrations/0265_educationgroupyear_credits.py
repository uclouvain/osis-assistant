# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-20 10:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0264_auto_20180420_1014'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationgroupyear',
            name='credits',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]