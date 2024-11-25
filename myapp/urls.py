from django.urls import path
from .views import (
    mypage, version, FlashCardSetList, FlashCardSetDetail,
    FlashCardList, CommentCreate, CommentList
)

urlpatterns = [
    path('v/', mypage, name='home'),  # Default core view
    path('', version, name='api-version'),  # Version API
    path('sets/', FlashCardSetList.as_view(), name='flashcard-set-list'),  # List or create sets
    path('sets/<int:setID>/', FlashCardSetDetail.as_view(), name='flashcard-set-detail'),  # Retrieve, update, or delete a set
    path('sets/<int:setID>/cards/', FlashCardList.as_view(), name='flashcard-list'),  # List or add flashcards in a set
    path('set/<int:setID>/comment/', CommentList.as_view(), name='comment-list'),  # List comments
    path('sets/<int:setID>/comments/add/', CommentCreate.as_view(), name='comment-create'),  # Add a comment
    #path('users/<int:userID>/sets'),
    #path('users/'),
    #path('users/<int:userID>/'),
    #path('users/<int:userID>/sets'),
    #path('users/<int:userID>/collections/'),
    ##path('users/<int:userID>/collections/<int:collectionID>'),
    #path('collections/'),
    #path('collections/random/'),
]