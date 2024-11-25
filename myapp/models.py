from django.db import models
from django.contrib.auth.models import User  # Import the default User model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

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
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="flashcard_sets", null=True)

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
    set = models.ForeignKey(FlashCardSet, on_delete=models.CASCADE, related_name="cards")

    def __str__(self):
        return f"FlashCard: {self.question}"


class Collection(models.Model):
    """Model representing a collection of flashcard sets by a user."""
    comment = models.TextField(blank=True, null=True, default="")
    set = models.ForeignKey(FlashCardSet, on_delete=models.SET_NULL, null=True, related_name="collections")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="collections")

    def __str__(self):
        return f"Collection by {self.author} on {self.set}"


class Comment(models.Model):
    """Model representing comments on a flashcard set."""
    comment = models.TextField()
    flashcard_set = models.ForeignKey(FlashCardSet, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="comments")

    def __str__(self):
        return f"Comment by {self.author}: {self.comment[:50]}..."


class DailyLimit(models.Model):
    """Model to track daily creation limits for flashcard sets and flashcards."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="daily_limit")
    sets_created_today = models.PositiveIntegerField(default=0)
    flashcards_created_today = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)

    def reset_if_needed(self):
        """Reset daily limits if the current date has changed."""
        if self.last_reset_date != now().date():
            self.sets_created_today = 0
            self.flashcards_created_today = 0
            self.last_reset_date = now().date()
            self.save(update_fields=["sets_created_today", "flashcards_created_today", "last_reset_date"])


# Signal to initialize DailyLimit when a new user is created
@receiver(post_save, sender=User)
def create_daily_limit(sender, instance, created, **kwargs):
    """Create a DailyLimit instance for a new user."""
    if created:
        DailyLimit.objects.create(user=instance)
