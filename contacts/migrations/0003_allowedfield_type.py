# Generated by Django 4.2.4 on 2023-10-18 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0002_allowedfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="allowedfield",
            name="type",
            field=models.CharField(
                choices=[
                    ("str", "Text"),
                    ("number", "Number"),
                    ("date", "Date"),
                    ("bool", "Boolean"),
                ],
                default="str",
                max_length=20,
            ),
        ),
    ]