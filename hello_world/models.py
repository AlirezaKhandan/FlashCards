from enum import Enum
from django.db import models

class FlashCards(models.Model):

    question = models.CharField(max_length = 200)
    answer = models.TextField()
    
    
    
class Difficulty(Enum): 
     Easy = "Easy"
     Medium = "Medium"
     Hard = "Hard"




class FlashCardSet(models.Model):
     id = models.IntegerField()
     name = models.TextField()
     cards = models.ManyToManyField()
     createdAt = models.DateTimeField()
     updatedAt = models.DateTimeField()
     comments = models.ManyToManyField()


class Error(models.Model):
     message = models.CharField()




class User(models.Model):
     userId = models.PositiveBigIntegerField()
     userName = models.CharField()
     admin = models.BooleanField(null=True, default=False)



#what the heck is this???????????????????????????
class Collection(models.Model):
    comment = models.TextField(blank=True, null=True, help_text="Example: 'I love this set!'")
    set = models.ForeignKey(FlashCardSet, on_delete=models.SET_NULL, null=True, blank=True, related_name='collections')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collections')

class Comment(models.Model):
     comment = models.CharField()
     set = models.CharField( null = True )
     author = models.CharField( null = True )





