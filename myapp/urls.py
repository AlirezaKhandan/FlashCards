from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    # Core Views
    mypage,
    modelsPage,
    version,
    register_user,
    registration_success,
    # Authentication
    # (Login and logout views are imported from django.contrib.auth.views)
    # Web Interface Views - Flashcard Sets
    FlashCardSetListView,
    FlashCardSetCreateView,
    FlashCardSetDetailView,
    FlashCardSetUpdateView,
    FlashCardSetDeleteView,
    # Web Interface Views - Flashcards
    FlashCardCreateView,
    FlashCardUpdateView,
    FlashCardDeleteView,
    # Web Interface Views - Comments
    CommentCreateView,
    CommentDeleteView,
    # Web Interface Views - Collections
    CollectionListView,
    CollectionCreateView,
    CollectionUpdateView,
    CollectionDeleteView,
    AddSetToCollectionView,
    RemoveSetFromCollectionView,
    # Search View
    SearchView,  # Updated import
    # Additional Views
    BrowseFlashCardSetListView,
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
)

urlpatterns = [
    # Homepage
    path('', mypage, name='home'),

    # API Version
    path('api/', version, name='api-version'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_user, name='register'),
    path('registration-success/', registration_success, name='registration-success'),

    # Web Interface - Flashcard Set Management
    path('sets/', FlashCardSetListView.as_view(), name='flashcard-set-list'),
    path('sets/add/', FlashCardSetCreateView.as_view(), name='flashcard-set-add'),
    path('sets/<int:pk>/', FlashCardSetDetailView.as_view(), name='flashcard-set-detail'),
    path('sets/<int:pk>/edit/', FlashCardSetUpdateView.as_view(), name='flashcard-set-edit'),
    path('sets/<int:pk>/delete/', FlashCardSetDeleteView.as_view(), name='flashcard-set-delete'),

    # Web Interface - Flashcard Management
    path('sets/<int:set_id>/cards/add/', FlashCardCreateView.as_view(), name='flashcard-add'),
    path('cards/<int:pk>/edit/', FlashCardUpdateView.as_view(), name='flashcard-edit'),
    path('cards/<int:pk>/delete/', FlashCardDeleteView.as_view(), name='flashcard-delete'),

    # Web Interface - Comments
    path('sets/<int:set_id>/comments/add/', CommentCreateView.as_view(), name='comment-add'),
    path('comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),

    # Web Interface - Collections
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/add/', CollectionCreateView.as_view(), name='collection-add'),
    path('collections/<int:pk>/edit/', CollectionUpdateView.as_view(), name='collection-edit'),
    path('collections/<int:pk>/delete/', CollectionDeleteView.as_view(), name='collection-delete'),
    # Add/Remove Sets to/from Collection
    path('sets/<int:set_id>/add-to-collection/', AddSetToCollectionView.as_view(), name='add-set-to-collection'),
    path('sets/<int:set_id>/remove-from-collection/', RemoveSetFromCollectionView.as_view(), name='remove-set-from-collection'),

    # Search
    path('search/', SearchView.as_view(), name='search'),  # Updated to use class-based view
    path('browse/', BrowseFlashCardSetListView.as_view(), name='browse-sets'),

    # API Endpoints
    # API - General
    path('api/', version, name='api-version'),

    # API - Flashcard Sets
    path('api/sets/', FlashCardSetListCreateAPIView.as_view(), name='api-sets'),
    path('api/sets/<int:setId>/', FlashCardSetRetrieveUpdateDestroyAPIView.as_view(), name='api-set-detail'),

    # API - Flashcards in a Set
    path('api/sets/<int:setId>/cards/', FlashCardListCreateAPIView.as_view(), name='api-set-cards'),
    path('api/sets/<int:setId>/cards/<int:cardId>/', FlashCardRetrieveUpdateDestroyAPIView.as_view(), name='api-card-detail'),

    # API - Comments on a Set
    path('api/sets/<int:setId>/comments/', CommentListCreateAPIView.as_view(), name='api-set-comments'),

    # API - Users
    path('api/users/', UserListCreateAPIView.as_view(), name='api-users'),
    path('api/users/<int:pk>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='api-user-detail'),
    path('api/users/<int:userId>/sets/', UserFlashCardSetListAPIView.as_view(), name='api-user-sets'),
    path('api/users/<int:userId>/collections/', UserCollectionListAPIView.as_view(), name='api-user-collections'),
    path('api/users/<int:userId>/collections/<int:collectionId>/', UserCollectionRetrieveUpdateDestroyAPIView.as_view(), name='api-user-collection-detail'),

    # API - Collections
    path('api/collections/', CollectionListCreateAPIView.as_view(), name='api-collections'),
    path('api/collections/random/', RandomCollectionRedirectView.as_view(), name='api-collections-random'),
]
