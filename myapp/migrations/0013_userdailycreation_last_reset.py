# Generated by Django 5.0.9 on 2024-12-17 19:29

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0012_alter_flashcard_answer_alter_flashcard_question"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdailycreation",
            name="last_reset",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
