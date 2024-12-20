# Generated by Django 5.0.9 on 2024-11-25 13:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0003_delete_error_alter_comment_author_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="flashcardset",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="flashcard_sets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="collections",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="comment",
            field=models.TextField(blank=True, default="", null=True),
        ),
        migrations.AlterField(
            model_name="collection",
            name="set",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="collections",
                to="myapp.flashcardset",
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="flashcard_set",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to="myapp.flashcardset",
            ),
        ),
        migrations.AlterField(
            model_name="flashcard",
            name="set",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cards",
                to="myapp.flashcardset",
            ),
        ),
        migrations.CreateModel(
            name="daily_limit",
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
                ("sets_created_today", models.PositiveIntegerField(default=0)),
                ("flashcards_created_today", models.PositiveIntegerField(default=0)),
                ("last_reset_date", models.DateField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="daily_limit",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
