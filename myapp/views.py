# Standard library imports
import random
import json
# Django imports
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.timezone import now, timedelta
from django.views import View
from django.views.generic import (
    CreateView, 
    DeleteView, 
    DetailView, 
    ListView, 
    TemplateView, 
    UpdateView,
)

# Django REST framework imports
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, Throttled, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Local app imports
from .forms import (
    CommentForm, 
    CollectionForm, 
    CustomUserCreationForm, 
    FlashCardForm, 
    FlashCardSetForm,
)
from .models import (
    Collection, 
    Comment, 
    CreationLimit, 
    FlashCard, 
    FlashCardSet, 
    Rating, 
    Tag, 
    User, 
    UserDailyCreation, 
    UserFavorite,
)
from .serializers import (
    CollectionSerializer, 
    CommentSerializer, 
    FlashCardSerializer, 
    FlashCardSetSerializer, 
    UserSerializer,
)
from .utils import get_average_rating





# Renders the homepage. If the user is logged in, show their most recent sets.
# Otherwise, show a general landing page.
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

# Renders a "registration success" page after a new user signs up.
# Simple confirmation view.
def registration_success(request):

    return render(request, 'registration_success.html')


@api_view(['GET'])
def version(request):
    # Returns the current API version in JSON format.
    # Used by the frontend footer or any client wanting API version info.
    return Response({"version": "1.0.0"})

def reset_limits_if_needed(user_daily):
    one_hour_ago = now() - timezone.timedelta(hours=1)
    if user_daily.last_reset < one_hour_ago:
        user_daily.flashcards_created = 0
        user_daily.sets_created = 0
        user_daily.collections_created = 0
        user_daily.last_reset = now()
        user_daily.save()

def within_limit(user_daily, creation_limit, item_type):
    if item_type == 'set':
        created = user_daily.sets_created
        limit = creation_limit.daily_set_limit
    elif item_type == 'flashcard':
        created = user_daily.flashcards_created
        limit = creation_limit.daily_flashcard_limit
    elif item_type == 'collection':
        created = user_daily.collections_created
        limit = creation_limit.daily_collection_limit
    else:
        return True, None

    if created >= limit:
        return False, f"You have reached your hourly {item_type} creation limit."
    else:
        # Warn if user is nearing limit 
        remaining = limit - created
        threshold = limit // 2
        warning_msg = None
        if remaining <= threshold and remaining > 0:
            warning_msg = (f"You are nearing your hourly {item_type} creation limit. "
                           f"You can only create {remaining} more {item_type}(s) this hour.")
        return True, warning_msg




def can_create_item(user, daily_field, limit_field, item_type_str):
    """
    Check if the user can create one more item (flashcard/set/collection).
    user: current user
    daily_field: str, name of the UserDailyCreation field ('sets_created', 'flashcards_created', 'collections_created')
    limit_field: str, name of the CreationLimit field ('daily_set_limit', 'daily_flashcard_limit', 'daily_collection_limit')
    item_type_str: str, human-readable type name ('set', 'collection', 'flashcard')

    Returns True if can create, False if limit exceeded.
    Also sets warning or error messages using Django messages.
    """
    today = timezone.now().date()
    user_daily, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
    creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)

    daily_created = getattr(user_daily, daily_field)
    limit = getattr(creation_limit, limit_field)

    # If limit is 0 or None, treat as no limit
    if limit == 0:
        return True

    # Check if limit exceeded
    if daily_created >= limit:
        messages.error(user, f"You have reached the daily {item_type_str} creation limit ({limit}).")
        return False

    # If halfway or beyond the limit, show a warning
    if daily_created >= limit / 2:
        left = limit - daily_created
        messages.warning(user, f"You are nearing your daily {item_type_str} creation limit. Only {left} {item_type_str}(s) left today.")

    return True



# Flashcard Set Views





# Lists all flashcard sets for the currently logged-in user.
class FlashCardSetListView(LoginRequiredMixin, ListView):
    model = FlashCardSet
    template_name = 'sets/list.html'
    context_object_name = 'sets'

    def get_queryset(self):
        return FlashCardSet.objects.filter(author=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType
        set_ct = ContentType.objects.get_for_model(FlashCardSet)
        favorite_entries = UserFavorite.objects.filter(user=self.request.user, content_type=set_ct)
        favorite_set_ids = set(favorite_entries.values_list('object_id', flat=True))
        context['favorite_set_ids'] = favorite_set_ids
        return context



# Allows a user to create a new flashcard set.
class FlashCardSetCreateView(LoginRequiredMixin, CreateView):
    model = FlashCardSet
    form_class = FlashCardSetForm
    template_name = 'sets/add.html'

    def form_valid(self, form):
        today = timezone.now().date()
        user = self.request.user
        user_daily, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
        creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)

        # Check daily set limit
        if user_daily.sets_created >= creation_limit.daily_set_limit and not user.is_superuser:
            messages.error(self.request, f"You have reached the daily limit of {creation_limit.daily_set_limit} sets.")
            return self.form_invalid(form)
        
        # If passed the check, create the set
        obj = form.save(commit=False)
        obj.author = user
        obj.save()

        # Increment daily count
        user_daily.sets_created += 1
        user_daily.save()

        # Redirect to sets list after creation
        return HttpResponseRedirect(reverse('flashcard-set-list'))





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

        # Retrieve comments for display
        content_type = ContentType.objects.get_for_model(FlashCardSet)
        comments = Comment.objects.filter(content_type=content_type, object_id=self.object.id).order_by('-created_at')
        context['comments'] = comments
        context['comment_form'] = CommentForm()

        # Calculate the average rating 
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

    def dispatch(self, request, *args, **kwargs):
        self.flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['pk'], author=self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Provide the flashcard set in the context so the template can access it
        context['set'] = self.flashcard_set
        return context

    def form_valid(self, form):
        user = self.request.user
        today = timezone.now().date()
        user_daily, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
        creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)

        # Check daily flashcard limit
        if user_daily.flashcards_created >= creation_limit.daily_flashcard_limit and not user.is_superuser:
            messages.error(self.request, f"You have reached the daily limit of {creation_limit.daily_flashcard_limit} flashcards.")
            return self.form_invalid(form)

        # Create the flashcard
        obj = form.save(commit=False)
        obj.set = self.flashcard_set
        obj.save()

        # Increment daily count
        user_daily.flashcards_created += 1
        user_daily.save()

        # Redirect to the add_more page after creation
        return HttpResponseRedirect(reverse('flashcard-add-more', kwargs={'pk': self.flashcard_set.pk}))






# Allows editing an existing flashcard.
# Only accessible to the set's author.
class FlashCardUpdateView(LoginRequiredMixin, UpdateView):
    model = FlashCard
    form_class = FlashCardForm
    template_name = 'cards/edit.html'

    def get_success_url(self):
        return reverse_lazy('flashcard-set-detail', kwargs={'pk': self.object.set.id})


# API Views



# Returns all comments for a given set ID.
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
    model = Comment
    template_name = 'comments/delete.html'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(author=self.request.user)

    def get_success_url(self):
        flashcard_set = self.object.flashcard_set
        if not flashcard_set:
            # If flashcard_set is None, comment should have a content_object that's a FlashCardSet
            if self.object.content_object and isinstance(self.object.content_object, FlashCardSet):
                flashcard_set = self.object.content_object
        if flashcard_set:
            return reverse_lazy('flashcard-set-detail', kwargs={'pk': flashcard_set.id})
        return reverse_lazy('flashcard-set-list')


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    fields = ['content']
    template_name = 'comments/edit.html'

    def get_queryset(self):
        # Only the author or superuser can edit
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(author=self.request.user)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if len(self.object.content) > 1000:
            form.add_error('content', "Comment cannot exceed 1000 characters.")
            return self.form_invalid(form)
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):

        flashcard_set = self.object.flashcard_set
        if not flashcard_set and self.object.content_object and isinstance(self.object.content_object, FlashCardSet):
            flashcard_set = self.object.content_object
        if flashcard_set:
            return reverse_lazy('flashcard-set-detail', kwargs={'pk': flashcard_set.id})
        return reverse_lazy('flashcard-set-list')



# Allows searching for flashcard sets and cards by keyword.
# Returns a list of sets matching the query.
class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'search/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()

        # If no query, return empty results
        if not query:
            context.update({
                'query': query,
                'your_materials': {'sets': [], 'collections': []},
                'sets': [],
                'collections': [],
                'tags': [],
                'users': []
            })
            return context

        # Find tags matching the query
        matching_tags = Tag.objects.filter(name__icontains=query)

        # Find sets matching by name, question in cards, or tags
        sets_query = FlashCardSet.objects.filter(
            Q(name__icontains=query) | 
            Q(cards__question__icontains=query) | 
            Q(tags__in=matching_tags)
        ).distinct()

        # Find collections by name
        collections_query = Collection.objects.filter(name__icontains=query)

        # Find users by username
        users_query = User.objects.filter(username__icontains=query)

        # Calculate ratings for sets
        rated_sets = []
        for s in sets_query:
            avg_rating = get_average_rating(s)  # This should return a float rating
            rated_sets.append({'object': s, 'rating': avg_rating})

        rated_collections = list(collections_query)
        found_tags = list(matching_tags)
        found_users = list(users_query)

        # Identify current user's sets and collections
        current_user = self.request.user
        user_sets = [rs for rs in rated_sets if rs['object'].author == current_user]
        user_collections = [c for c in rated_collections if c.author == current_user]

        your_materials = {
            'sets': user_sets,
            'collections': user_collections
        }

        # Other sets and collections not created by the user
        other_sets = [rs for rs in rated_sets if rs['object'].author != current_user]
        other_collections = [c for c in rated_collections if c.author != current_user]

        context.update({
            'query': query,
            'your_materials': your_materials,
            'sets': other_sets,
            'collections': other_collections,
            'tags': found_tags,
            'users': found_users
        })

        return context



    
# Updates an existing flashcard set.
# Checks permissions so only the author can update.
class FlashCardSetUpdateView(LoginRequiredMixin, UpdateView):
    model = FlashCardSet
    form_class = FlashCardSetForm
    template_name = 'sets/edit.html'

    def get_queryset(self):
        return FlashCardSet.objects.filter(author=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        # After the set is saved, handle tags
        tag_names = self.request.POST.get('tag_names', '')
        tag_list = [t.strip() for t in tag_names.split(',') if t.strip()]

        # Create any new tags not in DB
        from .models import Tag
        final_tags = []
        for name in tag_list:
            tag, created = Tag.objects.get_or_create(name=name)
            final_tags.append(tag)

        # Assign the tags to the instance
        self.object.tags.set(final_tags)
        return response

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
        user = self.request.user
        today = timezone.now().date()
        user_daily, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
        creation_limit, _ = CreationLimit.objects.get_or_create(pk=1)

        # Check daily collection limit
        if user_daily.collections_created >= creation_limit.daily_collection_limit and not user.is_superuser:
            messages.error(self.request, f"You have reached the daily limit of {creation_limit.daily_collection_limit} collections.")
            return self.form_invalid(form)

        # Create the collection
        obj = form.save(commit=False)
        obj.author = user
        obj.save()

        # Increment daily count
        user_daily.collections_created += 1
        user_daily.save()

        # Redirect to collections list after creation
        return HttpResponseRedirect(reverse('collection-list'))

    def form_invalid(self, form):
        return super().form_invalid(form)


# Deletes a collection.
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all sets owned by this user
        owned_sets = FlashCardSet.objects.filter(author=self.request.user)
        # Get current collection
        collection = self.object
        
        # Determine which sets are currently in this collection
        selected_set_ids = collection.sets.values_list('id', flat=True) if collection else []
        
        context['owned_sets'] = owned_sets
        context['selected_set_ids'] = selected_set_ids
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # After saving the collection, handle the sets
        selected_sets = self.request.POST.getlist('selected_sets')  # list of set IDs from the form
        # Filter the sets that the user owns and were selected
        updated_sets = FlashCardSet.objects.filter(author=self.request.user, id__in=selected_sets)
        
        # Update the collection sets
        self.object.sets.set(updated_sets)
        
        return response

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



# FlashCardSet API Views



# Lists all flashcard sets, and allows creating a new one if within daily limit.
class FlashCardSetListCreateAPIView(generics.ListCreateAPIView):
    queryset = FlashCardSet.objects.all()
    serializer_class = FlashCardSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        today = timezone.now().date()
        user_daily, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
        creation_limit = CreationLimit.objects.get(pk=1)

        if user_daily.sets_created >= creation_limit.daily_set_limit and not user.is_superuser:
            raise Throttled(detail=f"You have reached the daily limit of {creation_limit.daily_set_limit} sets.")

        tag_names = self.request.data.get('tag_names', '')
        tag_list = [t.strip() for t in tag_names.split(',') if t.strip()]
        if len(tag_list) > 8:
            raise ValidationError("A set cannot have more than 8 tags.")

        set_obj = serializer.save(author=user)
        user_daily.sets_created += 1
        user_daily.save()

        # Assign tags
        from .models import Tag
        tags = []
        for name in tag_list:
            tag_obj, created = Tag.objects.get_or_create(name=name)
            tags.append(tag_obj)
        set_obj.tags.set(tags)


# Retrieves, updates, or deletes a single flashcard set.
# Checks permissions to ensure only the author can modify or delete.
class FlashCardSetRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FlashCardSet.objects.all()
    serializer_class = FlashCardSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != self.get_object().author:
            raise PermissionDenied('You are not allowed to update this flashcard set.')
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
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


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
        user = self.request.user
        today = timezone.now().date()
        user_daily, _ = UserDailyCreation.objects.get_or_create(user=user, date=today)
        creation_limit = CreationLimit.objects.get(pk=1)

        if user_daily.collections_created >= creation_limit.daily_collection_limit and not user.is_superuser:
            raise Throttled(detail=f"You have reached the daily limit of {creation_limit.daily_collection_limit} collections.")

        # No sets required, no comment required; just save it
        serializer.save(author=user)
        user_daily.collections_created += 1
        user_daily.save()

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
    


class ToggleFavoriteView(LoginRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_type = request.data.get('type')
        item_id = request.data.get('id')

        if not item_type or not item_id:
            return Response({'success': False, 'error': 'Missing type or id'}, status=status.HTTP_400_BAD_REQUEST)

        if item_type != 'set':
            return Response({'success': False, 'error': 'Invalid type'}, status=status.HTTP_400_BAD_REQUEST)

        obj = get_object_or_404(FlashCardSet, pk=item_id)
        content_type = ContentType.objects.get_for_model(FlashCardSet)

        favorite_entry = UserFavorite.objects.filter(
            user=request.user, content_type=content_type, object_id=obj.id
        )

        if favorite_entry.exists():
            # Already favorite, so remove it
            favorite_entry.delete()
            return Response({'success': True, 'favorited': False}, status=status.HTTP_200_OK)
        else:
            # Not a favorite, add it
            UserFavorite.objects.create(user=request.user, content_type=content_type, object_id=obj.id)
            return Response({'success': True, 'favorited': True}, status=status.HTTP_200_OK)


class StudyModeView(LoginRequiredMixin, TemplateView):
    """Displays flashcards in study mode where the user can guess the answer."""
    template_name = 'sets/study.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flashcard_set = get_object_or_404(FlashCardSet, pk=self.kwargs['pk'])

        # Fetch flashcards from this set
        flashcards = list(flashcard_set.cards.values('question', 'answer'))

        # Convert flashcards to JSON so we can use them easily in JS
        context['flashcards_json'] = json.dumps(flashcards)
        context['set'] = flashcard_set
        return context