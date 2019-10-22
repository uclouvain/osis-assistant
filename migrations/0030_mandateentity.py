# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-19 10:56
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0156_offeryearentity_education_group_year'),
        ('assistant', '0029_auto_20170717_0859'),
    ]

    operations = [
        migrations.CreateModel(
            name='MandateEntity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assistant_mandate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assistant.AssistantMandate')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Entity')),
            ],
        ),
    ]
