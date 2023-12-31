# Generated by Django 4.2.4 on 2023-12-12 18:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("commons", "0002_exportlog_total_columns_exportlog_total_rows_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="exportlog",
            name="status",
            field=models.CharField(
                choices=[
                    ("running", "Running"),
                    ("failed", "Failed"),
                    ("completed", "Completed"),
                ],
                default="running",
                max_length=20,
            ),
        ),
    ]
