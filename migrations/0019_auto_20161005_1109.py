# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-10-05 09:09
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osis_common', '0006_modifications_documentfile'),
        ('assistant', '0018_auto_20160812_0920'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssistantDocumentFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assistant_mandate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assistant.AssistantMandate')),
                ('document_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osis_common.DocumentFile')),
            ],
        ),
        migrations.RemoveField(
            model_name='assistantdocument',
            name='assistant',
        ),
        migrations.RemoveField(
            model_name='assistantdocument',
            name='mandate',
        ),
        migrations.DeleteModel(
            name='AssistantDocument',
        ),
    ]
