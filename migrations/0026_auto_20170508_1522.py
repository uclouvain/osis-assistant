# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-08 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistant', '0025_remove_assistantmandate_grade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='academicassistant',
            name='inscription',
            field=models.CharField(choices=[('YES', 'YES'), ('NO', 'NO'), ('IN_PROGRESS', 'IN_PROGRESS')], default=None, max_length=12, null=True),
        ),
    ]