# Generated by Django 5.2 on 2025-04-09 18:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0004_corporatefiling_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="corporatefiling",
            name="category",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="corporatefiling",
            name="source",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
