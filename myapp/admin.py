from django.contrib import admin
from .models import (
    FlashCardSet, 
    FlashCard, 
    Collection, 
    Comment, 
    CreationLimit, 
    Rating, 
    UserDailyCreation,
    Tag,
    UserFavorite
)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(FlashCardSet)
class FlashCardSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'createdAt', 'updatedAt')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'createdAt', 'updatedAt')
    # If tags are a many-to-many field, they appear in a separate interface by default.
    # Could consider a filter_horizontal = ('tags',) if you want.
    filter_horizontal = ('tags',)

@admin.register(FlashCard)
class FlashCardAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'difficulty', 'set', 'created_at')
    search_fields = ('question', 'answer', 'set__name')
    list_filter = ('difficulty', 'set', 'created_at')

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'created_at')
    search_fields = ('name', 'author__username')
    filter_horizontal = ('sets',)
    list_filter = ('author', 'created_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'created_at', 'content_object')
    search_fields = ('author__username', 'content')
    list_filter = ('created_at',)

@admin.register(CreationLimit)
class CreationLimitAdmin(admin.ModelAdmin):
    # Only one record should exist. This ensures admin sees clearly.
    list_display = ('daily_flashcard_limit', 'daily_set_limit', 'daily_collection_limit')
    # Optional: if you want to prevent adding/deleting to keep it a true singleton:
    def has_add_permission(self, request):
        # If there's already an instance, no adding.
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion if you want a strict singleton
        return False

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'content_object')
    search_fields = ('user__username',)
    list_filter = ('score',)

@admin.register(UserDailyCreation)
class UserDailyCreationAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'flashcards_created', 'sets_created', 'collections_created')
    search_fields = ('user__username',)
    date_hierarchy = 'date'

@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'added_at')
    search_fields = ('user__username',)
    list_filter = ('added_at',)
