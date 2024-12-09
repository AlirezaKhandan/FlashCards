from django.contrib import admin
from .models import FlashCardSet, FlashCard, Collection, Comment, CreationLimit, Rating, UserDailyCreation
# Register your models here.


admin.site.register(FlashCardSet)
admin.site.register(FlashCard)
admin.site.register(Collection)
admin.site.register(Comment)
admin.site.register(CreationLimit)
admin.site.register(Rating)
admin.site.register(UserDailyCreation)