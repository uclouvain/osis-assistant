# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-24 07:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistant', '0037_messages_templates_update'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assistantmandate',
            name='position_id',
        ),
        migrations.AddField(
            model_name='review',
            name='comment_vice_rector',
            field=models.TextField(blank=True, null=True),
        ),
    ]
