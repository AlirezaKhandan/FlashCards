from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    mypage,
    modelsPage,
    version,
    register_user,
    FlashCardSetListView,
    FlashCardSetCreateView,
    FlashCardSetDetailView,
    FlashCardCreateView,
    FlashCardUpdateView,
    FlashCardDeleteView,
)


urlpatterns = [
    # Core Views
    path('v/', mypage, name='home'),  # Default core view
    path('m/', modelsPage, name='anotherpage'),
    path('', version, name='api-version'),  # Version API

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_user, name='register'),

    # Flashcard Set Management
    path('sets/', FlashCardSetListView.as_view(), name='flashcard-set-list'),  # View all sets
    path('sets/add/', FlashCardSetCreateView.as_view(), name='flashcard-set-add'),  # Add new set
    path('sets/<int:pk>/', FlashCardSetDetailView.as_view(), name='flashcard-set-detail'),  # View set details

    # Flashcard Management
    path('sets/<int:pk>/cards/add/', FlashCardCreateView.as_view(), name='flashcard-add'),  # Add new card to a set
    path('cards/<int:pk>/edit/', FlashCardUpdateView.as_view(), name='flashcard-edit'),  # Edit flashcard
    path('cards/<int:pk>/delete/', FlashCardDeleteView.as_view(), name='flashcard-delete'),  # Delete flashcard
]
