from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    # Core Views
    home_view,
    models_overview,
    version,
    user_registration_view,
    registration_success,


    # Web Interface - Flashcard Sets
    FlashCardSetListView,
    FlashCardSetCreateView,
    FlashCardSetDetailView,
    FlashCardSetUpdateView,
    FlashCardSetDeleteView,

    # Web Interface - Flashcards
    FlashCardCreateView,
    FlashCardUpdateView,
    FlashCardDeleteView,

    # Web Interface - Comments
    CommentCreateView,
    CommentDeleteView,

    # Web Interface - Collections
    CollectionListView,
    CollectionCreateView,
    CollectionUpdateView,
    CollectionDeleteView,
    AddSetToCollection,
    RemoveSetFromCollection,

    # Search and Browse
    SearchView,

    # Additional Web View
    FlashCardAddMoreView,

    # API Views
    FlashCardSetListCreateAPIView,
    FlashCardSetRetrieveUpdateDestroyAPIView,
    FlashCardListCreateAPIView,
    FlashCardRetrieveUpdateDestroyAPIView,
    CommentListCreateAPIView,
    UserListCreateAPIView,
    UserRetrieveUpdateDestroyAPIView,
    UserFlashCardSetListAPIView,
    UserCollectionListAPIView,
    UserCollectionRetrieveUpdateDestroyAPIView,
    CollectionListCreateAPIView,
    RandomCollectionRedirectView,
    AddToFavoritesView,
    UserFavouritesView,
    CommentUpdateView,

    # Rating
    RateItemView,
)

urlpatterns = [
    # Home and general views
    path('', home_view, name='home'),
    path('models/', models_overview, name='models-overview'),
    path('registration-success/', registration_success, name='registration-success'),

    # Authentication
    path('register/', user_registration_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Web Interface - Flashcard Sets
    path('sets/', FlashCardSetListView.as_view(), name='flashcard-set-list'),
    path('sets/add/', FlashCardSetCreateView.as_view(), name='flashcard-set-add'),
    path('sets/<int:pk>/', FlashCardSetDetailView.as_view(), name='flashcard-set-detail'),
    path('sets/<int:pk>/edit/', FlashCardSetUpdateView.as_view(), name='flashcard-set-edit'),
    path('sets/<int:pk>/delete/', FlashCardSetDeleteView.as_view(), name='flashcard-set-delete'),

    # Web Interface - Flashcards
    path('sets/<int:pk>/cards/add/', FlashCardCreateView.as_view(), name='flashcard-add'),
    path('cards/<int:pk>/edit/', FlashCardUpdateView.as_view(), name='flashcard-edit'),
    path('cards/<int:pk>/delete/', FlashCardDeleteView.as_view(), name='flashcard-delete'),
    path('sets/<int:pk>/add_more/', FlashCardAddMoreView.as_view(), name='flashcard-add-more'),
    path('favorites/', UserFavouritesView.as_view(), name='user-favourites'),


    # Web Interface - Comments
    path('sets/<int:pk>/comments/add/', CommentCreateView.as_view(), name='comment-add'),
    path('comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
    path('comments/<int:pk>/edit/', CommentUpdateView.as_view(), name='comment-edit'),


    # Web Interface - Collections
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/add/', CollectionCreateView.as_view(), name='collection-add'),
    path('collections/<int:pk>/edit/', CollectionUpdateView.as_view(), name='collection-edit'),
    path('collections/<int:pk>/delete/', CollectionDeleteView.as_view(), name='collection-delete'),
    path('sets/<int:pk>/add-to-collection/', AddSetToCollection.as_view(), name='add-set-to-collection'),
    path('sets/<int:pk>/remove-from-collection/', RemoveSetFromCollection.as_view(), name='remove-set-from-collection'),
    path('sets/addtofav/', AddToFavoritesView.as_view(), name='api-add-favorite'),

    # Search and Browse
    path('search/', SearchView.as_view(), name='search'),

    # API Version
    path('api/', version, name='api-version'),

    # API - Flashcard Sets
    path('api/sets/', FlashCardSetListCreateAPIView.as_view(), name='api-sets'),
    path('api/sets/<int:pk>/', FlashCardSetRetrieveUpdateDestroyAPIView.as_view(), name='api-set-detail'),

    # API - Flashcards in a Set
    path('api/sets/<int:pk>/cards/', FlashCardListCreateAPIView.as_view(), name='api-set-cards'),
    path('api/sets/<int:pk>/cards/<int:cardId>/', FlashCardRetrieveUpdateDestroyAPIView.as_view(), name='api-card-detail'),

    # API - Comments on a Set
    path('api/sets/<int:pk>/comments/', CommentListCreateAPIView.as_view(), name='api-set-comments'),

    # API - Users
    path('api/users/', UserListCreateAPIView.as_view(), name='api-users'),
    path('api/users/<int:pk>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='api-user-detail'),
    path('api/users/<int:userId>/sets/', UserFlashCardSetListAPIView.as_view(), name='api-user-sets'),
    path('api/users/<int:userId>/collections/', UserCollectionListAPIView.as_view(), name='api-user-collections'),
    path('api/users/<int:userId>/collections/<int:collectionId>/', UserCollectionRetrieveUpdateDestroyAPIView.as_view(), name='api-user-collection-detail'),

    # API - Collections
    path('api/collections/', CollectionListCreateAPIView.as_view(), name='api-collections'),
    path('api/collections/random/', RandomCollectionRedirectView.as_view(), name='api-collections-random'),

    # API - Rating
    path('rate/', RateItemView.as_view(), name='rate-item'),
]
