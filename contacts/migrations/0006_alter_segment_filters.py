# Generated by Django 4.2.4 on 2023-10-22 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0005_segment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='segment',
            name='filters',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
