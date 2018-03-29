# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-28 12:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistant', '0035_messages_templates_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewer',
            name='role',
            field=models.CharField(choices=[('PHD_SUPERVISOR', 'PHD_SUPERVISOR'), ('SUPERVISION', 'SUPERVISION'), ('SUPERVISION_ASSISTANT', 'SUPERVISION_ASSISTANT'), ('SUPERVISION_DAF', 'SUPERVISION_DAF'), ('SUPERVISION_DAF_ASSISTANT', 'SUPERVISION_DAF_ASSISTANT'), ('RESEARCH', 'RESEARCH'), ('RESEARCH_ASSISTANT', 'RESEARCH_ASSISTANT'), ('VICE_RECTOR', 'VICE_RECTOR'), ('VICE_RECTOR_ASSISTANT', 'VICE_RECTOR_ASSISTANT')], max_length=30),
        ),
    ]
