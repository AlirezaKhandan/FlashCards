# Generated by Django 5.0.9 on 2024-12-09 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0009_creationlimit_rename_comment_comment_content_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flashcard",
            name="difficulty",
            field=models.CharField(
                blank=True,
                choices=[("Easy", "easy"), ("Medium", "medium"), ("Hard", "hard")],
                max_length=10,
                null=True,
            ),
        ),
    ]