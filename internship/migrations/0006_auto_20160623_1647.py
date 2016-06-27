# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-06-23 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('internship', '0005_internshipoffer_selectable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='internshipmaster',
            name='internship_offer',
        ),
        migrations.RemoveField(
            model_name='internshipmaster',
            name='person',
        ),
        migrations.AddField(
            model_name='internshipmaster',
            name='first_name',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='internshipmaster',
            name='last_name',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='internshipmaster',
            name='civility',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='internshipmaster',
            name='speciality',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='internshipmaster',
            name='type_mastery',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='internshipoffer',
            name='selectable',
            field=models.BooleanField(default=True),
        ),
    ]