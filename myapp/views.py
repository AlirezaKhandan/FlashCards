from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
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
from rest_framework.permissions import IsAuthenticated
from .models import FlashCardSet, FlashCard, Comment, Collection, User, Rating, UserFavorite, Tag
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

from django.contrib.contenttypes.models import ContentType
from .forms import CommentForm
from django.db.models import Avg

from django.utils import timezone
from django.contrib import messages
from .models import CreationLimit, UserDailyCreation




# Renders the homepage. If the user is logged in, show their most recent sets.
# Otherwise, show a general landing page.
# Potential improvement: Could show public sets or a welcome message for guests
def home_view(request):
    
    if request.user.is_authenticated:
        flashcard_sets = FlashCardSet.objects.filter(author=request.user).order_by('-createdAt')[:6]  # Get the user's recent 6 sets
    else:
        flashcard_sets = None
    return render(request, 'index.html', {'flashcard_sets': flashcard_sets})


# Handles user registration by displaying a sign-up form and creating a new account.
# After successful registration, redirects to a success page.
def user_registration_view(request):
    
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
# Just renders a page that shows some info about models.
# Could be more descriptive or removed if not needed.
def models_overview(request):
    
    return render(request, 'models.html')

# Renders a "registration success" page after a new user signs up.
# Simple confirmation view.
def registration_success(request):

    return render(request, 'registration_success.html')


@api_view(['GET'])
def version(request):
    # Returns the current API version in JSON format.
    # Used by the frontend footer or any client wanting API version info.
    return Response({"version": "1.0.0"})





# Flashcard Set Views





# Lists all flashcard sets for the currently logged-in user.
# Straightforward: fetches sets authored by the user and displays them.
class FlashCardSetListView(LoginRequiredMixin, ListView):
    """List all flashcard sets for the logged-in user."""
    model = FlashCardSet
    template_name = 'sets/list.html'
    context_object_name = 'sets'

    def get_queryset(self):
        return FlashCardSet.objects.filter(author=self.request.user)


# Allows a user to create a new flashcard set.
# Enforces daily creation limits via UserDailyCreation and CreationLimit.
class FlashCardSetCreateView(LoginRequiredMixin, CreateView):
    
    model = FlashCardSet
    form_class = FlashCardSetForm
    template_name = 'sets/add.html'
    success_url = reverse_lazy('flashcard-set-list')

    # Check if user hit their daily set creation limit. If not, create the set.
    def form_valid(self, form):
        today = timezone.now().date()
        user_daily, _ = UserDailyCreation.objects.get_or_create(user=self.request.user, date=today)
        creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)

        if user_daily.sets_created >= creation_limit.daily_set_limit:
            return JsonResponse({'detail': 'Daily set limit exceeded.'}, status=429)

        form.instance.author = self.request.user
        response = super().form_valid(form)
        user_daily.sets_created += 1
        user_daily.save()
        return response


# Lets a user delete their own flashcard sets.
# Restricts deletion to sets authored by the current user.
class FlashCardSetDeleteView(LoginRequiredMixin, DeleteView):
    model = FlashCardSet
    success_url = reverse_lazy('flashcard-set-list')
    
    def get_queryset(self):
        # Only allow authors to delete their own sets
        return FlashCardSet.objects.filter(author=self.request.user)

# Lets a user delete a single flashcard from a set they own.
class FlashCardDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an existing flashcard."""
    model = FlashCard
    template_name = 'cards/delete.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.set.id})


# Shows details of a single flashcard set, including flashcards, comments, and average rating.
# Allows posting comments via POST.
class FlashCardSetDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific flashcard set."""
    model = FlashCardSet
    template_name = 'sets/detail.html'
    context_object_name = 'set'

     # Gathers flashcards, comments, and rating info for display
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve flashcards with 'id', 'question', 'answer', and now 'difficulty' to ensure the difficulty level is available in the JSON data
        context['flashcards'] = list(self.object.cards.values('id', 'question', 'answer', 'difficulty'))

        # Retrieve comments for display, ensuring that comments related to this set are shown
        content_type = ContentType.objects.get_for_model(FlashCardSet)
        comments = Comment.objects.filter(content_type=content_type, object_id=self.object.id).order_by('-created_at')
        context['comments'] = comments
        context['comment_form'] = CommentForm()

        # Calculate the average rating to provide user feedback on overall quality
        average_rating = Rating.objects.filter(content_type=content_type, object_id=self.object.id).aggregate(Avg('score'))['score__avg'] or 0
        context['average_rating'] = round(average_rating, 1)

        return context

    # Handles new comment submissions. If valid, redirects back to the set detail.
    def post(self, request, *args, **kwargs):
        if 'comment_form' in request.POST:
            self.object = self.get_object()
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.author = request.user
                comment.content_object = self.object
                comment.save()
                return redirect('flashcard-set-detail', pk=self.object.pk)
        return super().get(request, *args, **kwargs)





# Flashcard Views



# Allows user to add a new flashcard to a specific set, enforcing daily flashcard creation limit.
class FlashCardCreateView(LoginRequiredMixin, CreateView):
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/add.html'

    # Checks daily flashcard limit before saving.
    def form_valid(self, form):
        user = self.request.user
        today = timezone.now().date()
        user_daily_creation, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
        creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['pk'])

        if user_daily_creation.flashcards_created >= creation_limit.daily_flashcard_limit and not user.is_superuser:
            return JsonResponse({'detail': 'Daily flashcard limit exceeded.'}, status=429)

        else:
            form.instance.set = flashcard_set
            response = super().form_valid(form)
            user_daily_creation.flashcards_created += 1
            user_daily_creation.save()
            return response

    def get_success_url(self):
        return reverse_lazy('flashcard-add-more', kwargs={'pk': self.kwargs['pk']})


# Allows editing an existing flashcard.
# Only accessible to the set's author.
class FlashCardUpdateView(LoginRequiredMixin, UpdateView):
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/edit.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.set.id})


# API Views
class FlashCardSetList(APIView, PageNumberPagination):
    # This old API was previously enforcing daily limit using old logic.
    # Currently not in use after refactoring. If needed, update to new logic or remove
    # TODO: Update or remove this legacy endpoint. It's referencing daily_limit which no longer exists.
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

# TODO: Update to new logic or remove if not needed.
class FlashCardList(APIView, PageNumberPagination):
    def post(self, request, pk):
        user_limit = request.user.daily_limit
        user_limit.reset_if_needed()
        if user_limit.flashcards_created_today >= 50:
            return Response(
                {'error': 'You have reached the daily limit of 50 flashcards.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        flashcard_set = get_object_or_404(FlashCardSet, pk=pk, author=request.user)
        data = request.data
        data['set'] = pk
        serializer = FlashCardSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            user_limit.flashcards_created_today += 1
            user_limit.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Returns all comments for a given set ID.
# Likely needs updating to reflect the new generic comment structure if required.
class CommentList(APIView):
    
    def get(self, request, pk):
        flashcard_set = get_object_or_404(FlashCardSet, pk=pk)
        comments = Comment.objects.filter(flashcard_set=flashcard_set)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

# Creates a new comment on a flashcard set.
class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['comment']  
    template_name = 'comments/add.html'

    def form_valid(self, form):
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['pk'])
        form.instance.flashcard_set = flashcard_set
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.kwargs['pk']})

# Deletes an existing comment from a flashcard set.
class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an existing comment."""
    model = Comment
    template_name = 'comments/delete.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.flashcard_set.id})

# Allows searching for flashcard sets and cards by keyword.
# Returns a list of sets matching the query.
class SearchView(LoginRequiredMixin, ListView):
    template_name = 'search/results.html'
    context_object_name = 'results'

    def get_queryset(self):
        # By default, we'll treat `results` as flashcard sets
        query = self.request.GET.get('q')
        if query:
            # Find tags that match the query
            matching_tags = Tag.objects.filter(name__icontains=query)
            # Sets that match by name, card question or tags
            sets_query = FlashCardSet.objects.filter(
                Q(name__icontains=query) |
                Q(cards__question__icontains=query) |
                Q(tags__in=matching_tags)
            ).distinct()
            return sets_query
        return FlashCardSet.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            # Search users by username
            users = User.objects.filter(username__icontains=query)
            # Search collections by name
            collections = Collection.objects.filter(name__icontains=query)

            context['users'] = users
            context['collections'] = collections
            context['query'] = query
        else:
            context['users'] = []
            context['collections'] = []
            context['query'] = ""
        return context
    
# Updates an existing flashcard set.
# Checks permissions so only the author can update.
class FlashCardSetUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing flashcard set."""
    model = FlashCardSet
    form_class = FlashCardSetForm
    template_name = 'sets/edit.html' 

    def get_queryset(self):
        # Ensure that users can only edit their own sets
        return FlashCardSet.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('flashcard-set-list')


# Lists all collections belonging to the current user.
class CollectionListView(LoginRequiredMixin, ListView):
    model = Collection
    template_name = 'collections/list.html'
    context_object_name = 'collections'

    def get_queryset(self):
        return Collection.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        set_ct = ContentType.objects.get_for_model(FlashCardSet)
        favourites_count = UserFavorite.objects.filter(user=self.request.user, content_type=set_ct).count()
        context['favourites_count'] = favourites_count
        return context

# Creates a new collection for the current user.
class CollectionCreateView(LoginRequiredMixin, CreateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'collections/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('collection-list')

# Deletes a collection.
# If `delete_sets` is checked, deletes all sets in the collection too.
class CollectionDeleteView(LoginRequiredMixin, DeleteView):
    
    model = Collection
    template_name = 'collections/delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count how many sets the user has favorited
        set_ct = ContentType.objects.get_for_model(FlashCardSet)
        favourites_count = UserFavorite.objects.filter(user=self.request.user, content_type=set_ct).count()
        context['favourites_count'] = favourites_count
        return context

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



# Updates an existing collection owned by the user.
class CollectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'collections/update.html'

    def get_queryset(self):
        return Collection.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('collection-list')


# Adds a flashcard set to an existing collection.
# Only the collection's owner can add sets.
class AddSetToCollection(LoginRequiredMixin, View):
    def post(self, request, pk):
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id, author=request.user)
        flashcard_set = get_object_or_404(FlashCardSet, id=pk)
        collection.sets.add(flashcard_set)
        return redirect('flashcard-set-detail', pk=pk)

# Removes a flashcard set from a collection.
# Only the collection's owner can remove sets.
class RemoveSetFromCollection(LoginRequiredMixin, View):
    def post(self, request, pk):
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id, author=request.user)
        flashcard_set = get_object_or_404(FlashCardSet, id=pk)
        collection.sets.remove(flashcard_set)
        return redirect('flashcard-set-detail', pk=pk)

# Displays flashcard sets based on a search query, sorted by creation date.
class BrowseSetsView(ListView):
    
    model = FlashCardSet
    template_name = 'sets/browse_list.html'
    context_object_name = 'sets'
    # TODO:Optional: adds pagination
    paginate_by = 10  

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return FlashCardSet.objects.filter(name__icontains=query).order_by('-createdAt')
        else:
            return FlashCardSet.objects.none()

    



# FlashCardSet API Views



# Lists all flashcard sets, and allows creating a new one if within daily limit.
class FlashCardSetListCreateAPIView(generics.ListCreateAPIView):
    queryset = FlashCardSet.objects.all()
    serializer_class = FlashCardSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Checks the daily set limit before creating a new set.
    def perform_create(self, serializer):
        today = timezone.now().date()
        user = self.request.user
        user_daily_creation, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)

        # Fetch the creation limit directly
        creation_limit = CreationLimit.objects.get(pk=1)

        if user_daily_creation.sets_created >= creation_limit.daily_set_limit and not user.is_superuser:
            raise Throttled(detail='You have reached the daily limit of {} flashcard sets.'.format(creation_limit.daily_set_limit))
        
        # If not exceeded
        serializer.save(author=user)
        user_daily_creation.sets_created += 1
        user_daily_creation.save()


# Retrieves, updates, or deletes a single flashcard set.
# Checks permissions to ensure only the author can modify or delete.
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



# Lists flashcards for a given set and allows creating new ones if not hitting the daily limit.
class FlashCardListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FlashCardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        pk = self.kwargs['pk']
        return FlashCard.objects.filter(set_id=pk)

    def perform_create(self, serializer):
        user = self.request.user
        today = timezone.now().date()

        pk = self.kwargs['pk']
        flashcard_set = get_object_or_404(FlashCardSet, id=pk)

        # Get or create the UserDailyCreation instance for the user and today
        user_daily_creation, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)

        # Get the global creation limits
        creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)

        # Check if the user has exceeded the daily flashcard creation limit
        if user_daily_creation.flashcards_created >= creation_limit.daily_flashcard_limit and not user.is_superuser:
            raise Throttled(detail='You have reached the daily limit of {} flashcards.'.format(creation_limit.daily_flashcard_limit))
        else:
            serializer.save(set=flashcard_set)
            user_daily_creation.flashcards_created += 1
            user_daily_creation.save()

# Retrieves, updates, or deletes a single flashcard.
# Usually restricted to the set's author.
class FlashCardRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FlashCard.objects.all()
    serializer_class = FlashCardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]



# Comment API Views


# Lists comments for a given set and allows creating new ones.
# TODO: Update to handle generic comments if necessary.
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        pk = self.kwargs['pk']
        return Comment.objects.filter(flashcard_set_id=pk)

    def perform_create(self, serializer):
        pk = self.kwargs['pk']
        flashcard_set = get_object_or_404(FlashCardSet, id=pk)
        serializer.save(flashcard_set=flashcard_set, author=self.request.user)



# User API Views


# Lists all users and creates new users.
# For user creation, ensure proper password handling and error responses.
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Retrieves, updates, or deletes a user by ID.
# Restrict certain fields (like admin status) to admin-only modifications.
class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer



# User's FlashCardSets



# Lists all flashcard sets created by a specific user.
class UserFlashCardSetListAPIView(generics.ListAPIView):
    serializer_class = FlashCardSetSerializer

    def get_queryset(self):
        user_id = self.kwargs['userId']
        return FlashCardSet.objects.filter(author_id=user_id)



# User's Collections


# Lists all collections created by a specific user.
class UserCollectionListAPIView(generics.ListAPIView):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        user_id = self.kwargs['userId']
        return Collection.objects.filter(author_id=user_id)

# Retrieves, updates, or deletes a specific collection by a user.
# Ensure permission checks are in place.
class UserCollectionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]




# Collections API Views



# Lists all collections and allows creating new ones.
# Associates the new collection with the current user.
class CollectionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

# Redirects to a random collection's detail page if collections exist.
# Otherwise returns a 404.
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
        


# Handles rating a set or flashcard. User selects a score and it updates the rating.
# Returns JSON with the new average rating.
class RateItemView(LoginRequiredMixin, View):
    def post(self, request):
        score = int(request.POST.get('score'))
        model_name = request.POST.get('model')
        object_id = int(request.POST.get('object_id'))

        content_type = ContentType.objects.get(model=model_name)
        obj = content_type.get_object_for_this_type(id=object_id)

        # Save or update the rating
        Rating.objects.update_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            defaults={'score': score}
        )

        # Calculate new average rating
        average_rating = Rating.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).aggregate(Avg('score'))['score__avg']

        return JsonResponse({'average_rating': average_rating})
    

# After successfully adding a flashcard, shows a page with options to add another or return to the set.
class FlashCardAddMoreView(LoginRequiredMixin, TemplateView):
    template_name = 'cards/add_more.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['pk'])
        context['set'] = flashcard_set
        return context
    



class AddToFavoritesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Expects JSON: { "type": "<set|collection>", "id": <int> }
        Adds the specified item to the user's favorites if not already there.
        """
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        if not item_type or not item_id:
            return Response({'success': False, 'error': 'Missing type or id'}, status=status.HTTP_400_BAD_REQUEST)

        # Determine the model based on type
        if item_type == 'set':
            model = FlashCardSet
        elif item_type == 'collection':
            model = Collection
        else:
            return Response({'success': False, 'error': 'Invalid type'}, status=status.HTTP_400_BAD_REQUEST)

        # Get object
        obj = get_object_or_404(model, pk=item_id)
        
        # Check if already in favorites
        content_type = ContentType.objects.get_for_model(model)
        favorite_exists = UserFavorite.objects.filter(
            user=request.user, content_type=content_type, object_id=obj.id
        ).exists()

        if favorite_exists:
            return Response({'success': False, 'error': 'Already in favorites'}, status=status.HTTP_400_BAD_REQUEST)

        # Add to favorites
        UserFavorite.objects.create(user=request.user, content_type=content_type, object_id=obj.id)
        return Response({'success': True}, status=status.HTTP_201_CREATED)
    

class UserFavouritesView(LoginRequiredMixin, TemplateView):
    template_name = 'sets/favourites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType
        from .models import UserFavorite
        
        set_ct = ContentType.objects.get_for_model(FlashCardSet)
        favourite_entries = UserFavorite.objects.filter(user=self.request.user, content_type=set_ct)
        set_ids = favourite_entries.values_list('object_id', flat=True)
        favourite_sets = FlashCardSet.objects.filter(pk__in=set_ids)
        context['favourite_sets'] = favourite_sets
        return context