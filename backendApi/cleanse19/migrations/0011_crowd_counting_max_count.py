# Generated by Django 3.1.7 on 2021-05-13 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cleanse19', '0010_crowdcountinganalysis_facemaskanalysis_socialdistancinganalysis'),
    ]

    operations = [
        migrations.AddField(
            model_name='crowd_counting',
            name='max_count',
            field=models.IntegerField(default=0),
        ),
    ]
