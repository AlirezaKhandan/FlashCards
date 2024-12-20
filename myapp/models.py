from django.db import models
from django.contrib.auth.models import User  # Import the default User model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

# Choices for difficulty levels
class Difficulty(models.TextChoices):
    EASY = "Easy", "easy"
    MEDIUM = "Medium", "medium"
    HARD = "Hard", "hard"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.name

class FlashCardSet(models.Model):
    """Model representing a set of flashcards."""
    name = models.CharField(max_length=255)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="flashcard_sets",
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(Tag, related_name="sets", blank=True)

    def clean(self):
        super().clean()
        #  no more than 8 tags are associated
        if self.pk and self.tags.count() > 8:
            raise ValidationError("A set cannot have more than 8 tags.")

    def __str__(self):
        return f"FlashCardSet: {self.name}"


class FlashCard(models.Model):
    """Model representing a single flashcard."""
    question = models.CharField(max_length=255, default="")
    answer = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, null=True,blank=True)
    set = models.ForeignKey(FlashCardSet, related_name="cards", on_delete=models.CASCADE)

    def __str__(self):
        return f"FlashCard: {self.question}"


class Collection(models.Model):
    """Model representing a collection of flashcard sets by a user."""
    name = models.CharField(max_length=255, default='')
    description = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="collections",
        null=False,  
        blank=False
    )
    sets = models.ManyToManyField(FlashCardSet, related_name='collections')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Collection '{self.name}' by {self.author.username}"


# A generic UserFavorite model to store user favorites (sets, collections, etc.)
class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'content_type', 'object_id']),
        ]
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"{self.user.username}'s favorite: {self.content_object}"
    

class Comment(models.Model):
    """Model representing comments on a flashcard set or collection."""
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="comments",
        null=True,
        blank=True
    )
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    flashcard_set = models.ForeignKey(
        FlashCardSet,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,  
        blank=True
    )
    #
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        author_name = self.author.username if self.author else "Unknown Author"
        return f"Comment by {author_name} on {self.content_object}"


class CreationLimit(models.Model):
    """Singleton model to store global creation limits adjustable by admin."""
    daily_flashcard_limit = models.PositiveIntegerField(default=20)
    daily_set_limit = models.PositiveIntegerField(default=5)
    daily_collection_limit = models.PositiveIntegerField(default=5)

    def save(self, *args, **kwargs):
        self.pk = 1 
        super().save(*args, **kwargs)

    def __str__(self):
        return "Global Creation Limits"
    


class Rating(models.Model):
    """Model representing a rating for a flashcard set or flashcard."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    score = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"Rating {self.score} by {self.user.username} for {self.content_object}"

class UserDailyCreation(models.Model):
    """Model to track daily creation counts for each user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_creations')
    last_reset = models.DateTimeField(default=timezone.now)
    date = models.DateField(default=timezone.now)
    flashcards_created = models.PositiveIntegerField(default=0)
    sets_created = models.PositiveIntegerField(default=0)
    collections_created = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Daily creations for {self.user.username} on {self.date}"
