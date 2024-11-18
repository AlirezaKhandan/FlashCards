from enum import Enum
from django.db import models

    
class Difficulty(models.TextChoices):
    EASY = "Easy", "Easy"
    MEDIUM = "Medium", "Medium"
    HARD = "Hard", "Hard"




class FlashCardSet(models.Model):
     id = models.AutoField(primary_key = True)
     name = models.CharField(max_length = 255)
     createdAt = models.DateTimeField(auto_now_add=True)
     updatedAt = models.DateTimeField(auto_now=True)
     #comments = models.ManyToManyField('Comment') Do i need to have this???????
     def __str__(self):
        return f"FlashCardSet: {self.name}"


class FlashCard(models.Model):
    question = models.CharField(max_length=255, default="Default Question")
    answer = models.CharField(max_length=255, default="Default Answer")
    difficulty = models.CharField(
        max_length=10, 
        choices=Difficulty.choices,
        null=True,
        blank=True 
    )
    set = models.ForeignKey(FlashCardSet)
    def __str__(self):
        return f"{self.question}"
 

class Error(models.Model): 
     message = models.CharField(max_length = 255)



class User(models.Model):
     userId = models.PositiveBigIntegerField(unique = True)
     userName = models.CharField(max_length = 150)
     admin = models.BooleanField(null=True, default=False)
     def __str__(self):
        return self.userName



# what the heck is this????????????????????????????
class Collection(models.Model):
    comment = models.TextField(blank=True, null=True)
    set = models.ForeignKey(FlashCardSet, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Collection by {self.author} on {self.set}"



class Comment(models.Model):
    comment = models.TextField()
    flashcard_set = models.ForeignKey('FlashCardSet', on_delete=models.CASCADE)
    author = models.ForeignKey('User', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Comment by {self.author}: {self.comment[:50]}..."