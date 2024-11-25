from django.db import models
from django.contrib.auth.models import User  # Import the default User model

# Choices for difficulty levels
class Difficulty(models.TextChoices):
    EASY = "Easy", "Easy"
    MEDIUM = "Medium", "Medium"
    HARD = "Hard", "Hard"


class FlashCardSet(models.Model):
    """Model representing a set of flashcards."""
    name = models.CharField(max_length=255)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FlashCardSet: {self.name}"


class FlashCard(models.Model):
    """Model representing a single flashcard."""
    question = models.CharField(max_length=255, default="Default Question")
    answer = models.CharField(max_length=255, default="Default Answer")
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        null=True,
        blank=True,
    )
    set = models.ForeignKey(FlashCardSet, on_delete=models.CASCADE)

    def __str__(self):
        return f"FlashCard: {self.question}"


class Collection(models.Model):
    """Model representing a collection of flashcard sets by a user."""
    comment = models.TextField(blank=True, null=True)
    set = models.ForeignKey(FlashCardSet, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Collection by {self.author} on {self.set}"


class Comment(models.Model):
    """Model representing comments on a flashcard set."""
    comment = models.TextField()
    flashcard_set = models.ForeignKey(FlashCardSet, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Comment by {self.author}: {self.comment[:50]}..."
