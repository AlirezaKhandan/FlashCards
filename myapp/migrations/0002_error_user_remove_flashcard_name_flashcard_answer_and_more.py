# Generated by Django 5.0.9 on 2024-11-15 16:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Error",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("message", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("userId", models.PositiveBigIntegerField(unique=True)),
                ("userName", models.CharField(max_length=150)),
                ("admin", models.BooleanField(default=False, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="flashcard",
            name="name",
        ),
        migrations.AddField(
            model_name="flashcard",
            name="answer",
            field=models.CharField(default="Default Answer", max_length=255),
        ),
        migrations.AddField(
            model_name="flashcard",
            name="difficulty",
            field=models.CharField(
                blank=True,
                choices=[("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")],
                max_length=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flashcard",
            name="question",
            field=models.CharField(default="Default Question", max_length=255),
        ),
        migrations.CreateModel(
            name="FlashCardSet",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
                ("updatedAt", models.DateTimeField(auto_now=True)),
                (
                    "cards",
                    models.ManyToManyField(related_name="sets", to="myapp.flashcard"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("comment", models.TextField()),
                (
                    "flashcard_set",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="myapp.flashcardset",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="myapp.user",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("comment", models.TextField(blank=True, null=True)),
                (
                    "set",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="myapp.flashcardset",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="myapp.user",
                    ),
                ),
            ],
        ),
    ]
