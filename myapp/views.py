from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import FlashCardSet, FlashCard, Comment, DailyLimit
from .serializers import FlashCardSetSerializer, FlashCardSerializer, CommentSerializer
from .forms import FlashCardSetForm, FlashCardForm


# Core Views
def mypage(request):
    """Render the homepage."""
    return render(request, 'index.html')


def register_user(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            DailyLimit.objects.create(user=user)  # Initialize daily limit
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def modelsPage(request):
    """Render the models page."""
    return render(request, 'models.html')


@api_view(['GET'])
def version(request):
    """API to get the current version."""
    return Response({"version": "1.0.0"})


# Flashcard Set Views
class FlashCardSetListView(LoginRequiredMixin, ListView):
    """List all flashcard sets for the logged-in user."""
    model = FlashCardSet
    template_name = 'sets/list.html'
    context_object_name = 'sets'

    def get_queryset(self):
        return FlashCardSet.objects.filter(author=self.request.user)


class FlashCardSetCreateView(LoginRequiredMixin, CreateView):
    """Create a new flashcard set with daily limit checks."""
    model = FlashCardSet
    form_class = FlashCardSetForm
    template_name = 'sets/add.html'
    success_url = reverse_lazy('flashcard-set-list')

    def form_valid(self, form):
        user_limit = self.request.user.daily_limit
        user_limit.reset_if_needed()
        if user_limit.sets_created_today >= 5:
            return JsonResponse(
                {'error': 'You have reached the daily limit of 5 flashcard sets.'}, 
                status=429
            )
        form.instance.author = self.request.user
        user_limit.sets_created_today += 1
        user_limit.save()
        return super().form_valid(form)

class FlashCardDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an existing flashcard."""
    model = FlashCard
    template_name = 'cards/delete.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.set.id})


class FlashCardSetDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific flashcard set."""
    model = FlashCardSet
    template_name = 'sets/detail.html'
    context_object_name = 'set'


# Flashcard Views
class FlashCardCreateView(LoginRequiredMixin, CreateView):
    """Add a new flashcard to a set with daily limit checks."""
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/add.html'

    def form_valid(self, form):
        user_limit = self.request.user.daily_limit
        user_limit.reset_if_needed()
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['pk'])
        if user_limit.flashcards_created_today >= 50:
            return JsonResponse(
                {'error': 'You have reached the daily limit of 50 flashcards.'}, 
                status=429
            )
        form.instance.set = flashcard_set
        user_limit.flashcards_created_today += 1
        user_limit.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.kwargs['pk']})


class FlashCardUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing flashcard."""
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/edit.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.set.id})


# API Views
class FlashCardSetList(APIView, PageNumberPagination):
    """API for listing and creating flashcard sets."""
    def get(self, request):
        flashcard_sets = FlashCardSet.objects.filter(author=request.user)
        results = self.paginate_queryset(flashcard_sets, request, view=self)
        serializer = FlashCardSetSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FlashCardSetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlashCardList(APIView, PageNumberPagination):
    """API for listing and creating flashcards in a set."""
    def get(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id, author=request.user)
        flashcards = FlashCard.objects.filter(set=flashcard_set)
        results = self.paginate_queryset(flashcards, request, view=self)
        serializer = FlashCardSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id, author=request.user)
        data = request.data
        data['set'] = set_id
        serializer = FlashCardSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentList(APIView):
    """API for listing comments on a flashcard set."""
    def get(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id)
        comments = Comment.objects.filter(flashcard_set=flashcard_set)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
