# Generated by Django 5.0.9 on 2024-12-14 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0011_tag_flashcardset_tags_userfavorite"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flashcard",
            name="answer",
            field=models.CharField(default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="flashcard",
            name="question",
            field=models.CharField(default="", max_length=255),
        ),
    ]
