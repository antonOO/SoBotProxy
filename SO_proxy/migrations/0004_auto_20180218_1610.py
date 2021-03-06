# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2018-02-18 16:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SO_proxy', '0003_auto_20180215_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingdata',
            name='ascore',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='trainingdata',
            name='is_accepted_answer',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='trainingdata',
            name='qscore',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='trainingdata',
            name='view_count',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
