from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.views import View  # Import View for the create view
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import Throttled

from .models import FlashCardSet, FlashCard, Comment, DailyLimit, Collection, User
from .serializers import FlashCardSetSerializer, FlashCardSerializer, CommentSerializer, CollectionSerializer, UserSerializer
from .forms import FlashCardSetForm, FlashCardForm, CustomUserCreationForm, CollectionForm

from django.db.models import Q
from django.contrib.auth import authenticate

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.urls import reverse
import random



# Core Views
def mypage(request):
    """Render the homepage."""
    if request.user.is_authenticated:
        flashcard_sets = FlashCardSet.objects.filter(author=request.user).order_by('-createdAt')[:6]  # Get the user's recent 6 sets
    else:
        flashcard_sets = None
    return render(request, 'index.html', {'flashcard_sets': flashcard_sets})


def register_user(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Redirect to registration success page
            return redirect('registration-success')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})



@login_required
def modelsPage(request):
    """Render the models page."""
    return render(request, 'models.html')


def registration_success(request):
    return render(request, 'registration_success.html')


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

class FlashCardSetDeleteView(LoginRequiredMixin, DeleteView):
    model = FlashCardSet
    success_url = reverse_lazy('flashcard-set-list')
    
    def get_queryset(self):
        # Only allow authors to delete their own sets
        return FlashCardSet.objects.filter(author=self.request.user)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prepare flashcards data for JSON serialization
        context['flashcards'] = list(self.object.cards.values('id', 'question', 'answer'))
        return context


# Flashcard Views
class FlashCardCreateView(LoginRequiredMixin, CreateView):
    """Add a new flashcard to a set with daily limit checks."""
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/add.html'

    def form_valid(self, form):
        user_limit = self.request.user.daily_limit
        user_limit.reset_if_needed()
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['set_id'])
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
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.kwargs['set_id']})


class FlashCardUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing flashcard."""
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/edit.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.set.id})


# API Views
class FlashCardSetList(APIView, PageNumberPagination):
    def post(self, request):
        user_limit = request.user.daily_limit
        user_limit.reset_if_needed()
        if user_limit.sets_created_today >= 5:
            return Response(
                {'error': 'You have reached the daily limit of 5 flashcard sets.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        serializer = FlashCardSetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            user_limit.sets_created_today += 1
            user_limit.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlashCardList(APIView, PageNumberPagination):
    def post(self, request, set_id):
        user_limit = request.user.daily_limit
        user_limit.reset_if_needed()
        if user_limit.flashcards_created_today >= 50:
            return Response(
                {'error': 'You have reached the daily limit of 50 flashcards.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id, author=request.user)
        data = request.data
        data['set'] = set_id
        serializer = FlashCardSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            user_limit.flashcards_created_today += 1
            user_limit.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentList(APIView):
    """API for listing comments on a flashcard set."""
    def get(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id)
        comments = Comment.objects.filter(flashcard_set=flashcard_set)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Add a new comment to a flashcard set."""
    model = Comment
    fields = ['comment']  # Only the comment field
    template_name = 'comments/add.html'

    def form_valid(self, form):
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['set_id'])
        form.instance.flashcard_set = flashcard_set
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.kwargs['set_id']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an existing comment."""
    model = Comment
    template_name = 'comments/delete.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.flashcard_set.id})


class SearchView(LoginRequiredMixin, ListView):
    """Search for flashcard sets or flashcards."""
    template_name = 'search/results.html'
    context_object_name = 'results'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return FlashCardSet.objects.filter(
                Q(name__icontains=query) | Q(cards__question__icontains=query)
            ).distinct()
        return FlashCardSet.objects.none()
    

class FlashCardSetUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing flashcard set."""
    model = FlashCardSet
    form_class = FlashCardSetForm
    template_name = 'sets/edit.html'  # Create this template

    def get_queryset(self):
        # Ensure that users can only edit their own sets
        return FlashCardSet.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.pk})


class CollectionListView(LoginRequiredMixin, ListView):
    """Display all collections for the logged-in user."""
    model = Collection
    template_name = 'collections/list.html'
    context_object_name = 'collections'

    def get_queryset(self):
        return Collection.objects.filter(author=self.request.user)

class CollectionCreateView(LoginRequiredMixin, CreateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'collections/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('collection-list')


class CollectionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a collection."""
    model = Collection
    template_name = 'collections/delete.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        delete_sets = request.POST.get('delete_sets') == 'on'
        if delete_sets:
            # Delete all sets in the collection
            self.object.sets.all().delete()
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Collection.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('collection-list')




class CollectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'collections/update.html'

    def get_queryset(self):
        return Collection.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('collection-list')


class AddSetToCollectionView(LoginRequiredMixin, View):
    def post(self, request, set_id):
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id, author=request.user)
        flashcard_set = get_object_or_404(FlashCardSet, id=set_id)
        collection.sets.add(flashcard_set)
        return redirect('flashcard-set-detail', pk=set_id)

class RemoveSetFromCollectionView(LoginRequiredMixin, View):
    def post(self, request, set_id):
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id, author=request.user)
        flashcard_set = get_object_or_404(FlashCardSet, id=set_id)
        collection.sets.remove(flashcard_set)
        return redirect('flashcard-set-detail', pk=set_id)


class BrowseFlashCardSetListView(ListView):
    """View to display flashcard sets based on search query."""
    model = FlashCardSet
    template_name = 'sets/browse_list.html'
    context_object_name = 'sets'
    paginate_by = 10  # Optional: adds pagination

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return FlashCardSet.objects.filter(name__icontains=query).order_by('-createdAt')
        else:
            return FlashCardSet.objects.none()

    

# FlashCardSet API Views
class FlashCardSetListCreateAPIView(generics.ListCreateAPIView):
    queryset = FlashCardSet.objects.all()
    serializer_class = FlashCardSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user_limit, _ = DailyLimit.objects.get_or_create(user=self.request.user)
        user_limit.reset_if_needed()
        if user_limit.sets_created_today >= 5 and not self.request.user.is_superuser:
            raise Throttled(detail='You have reached the daily limit of 5 flashcard sets.')
        else:
            serializer.save(author=self.request.user)
            user_limit.sets_created_today += 1
            user_limit.save()

class FlashCardSetRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FlashCardSet.objects.all()
    serializer_class = FlashCardSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != self.get_object().author:
            return Response(
                {'error': 'You are not allowed to update this flashcard set.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author:
            return Response(
                {'error': 'You are not allowed to delete this flashcard set.'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()

# FlashCard API Views
class FlashCardListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FlashCardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        set_id = self.kwargs['setId']
        return FlashCard.objects.filter(set_id=set_id)

    def perform_create(self, serializer):
        set_id = self.kwargs['setId']
        flashcard_set = get_object_or_404(FlashCardSet, id=set_id)
        user_limit, _ = DailyLimit.objects.get_or_create(user=self.request.user)
        user_limit.reset_if_needed()
        if user_limit.flashcards_created_today >= 50 and not self.request.user.is_superuser:
            raise Throttled(detail='You have reached the daily limit of 50 flashcards.')
        else:
            serializer.save(set=flashcard_set)
            user_limit.flashcards_created_today += 1
            user_limit.save()


class FlashCardRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FlashCard.objects.all()
    serializer_class = FlashCardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Comment API Views
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        set_id = self.kwargs['setId']
        return Comment.objects.filter(flashcard_set_id=set_id)

    def perform_create(self, serializer):
        set_id = self.kwargs['setId']
        flashcard_set = get_object_or_404(FlashCardSet, id=set_id)
        serializer.save(flashcard_set=flashcard_set, author=self.request.user)

# User API Views
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# User's FlashCardSets
class UserFlashCardSetListAPIView(generics.ListAPIView):
    serializer_class = FlashCardSetSerializer

    def get_queryset(self):
        user_id = self.kwargs['userId']
        return FlashCardSet.objects.filter(author_id=user_id)

# User's Collections
class UserCollectionListAPIView(generics.ListAPIView):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        user_id = self.kwargs['userId']
        return Collection.objects.filter(author_id=user_id)

class UserCollectionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Collections API Views
class CollectionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class RandomCollectionRedirectView(APIView):
    def get(self, request):
        collections = Collection.objects.all()
        if collections.exists():
            random_collection = random.choice(collections)
            return redirect(reverse('api-user-collection-detail', kwargs={
                'userId': random_collection.author.id,
                'collectionId': random_collection.id
            }))
        else:
            return Response({'error': 'There are no flashcard set collections'}, status=status.HTTP_404_NOT_FOUND)