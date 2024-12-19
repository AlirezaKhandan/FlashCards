from rest_framework import serializers
from .models import FlashCardSet, FlashCard, Comment, Collection
from django.contrib.auth.models import User  # Use Django's default User model


# This serializer provides a read-only view of the user’s basic info:
# - id and username for identification
# - a calculated field 'admin' to indicate if the user is a superuser
class UserSerializer(serializers.ModelSerializer):
    admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'admin']

    # Return True if the user is a superuser, otherwise False.
    # This helps consumers of the API know if the user has admin privileges.
    def get_admin(self, obj):
        return obj.is_superuser


# Serializes flashcard details:
# - question, answer, difficulty
# Designed to be nested inside a set serializer to show all flashcards in a set.
class FlashCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashCard
        fields = ['id', 'question', 'answer', 'difficulty']


# Serializes a comment, including:
# - The comment text
# - Nested author details for clarity
# Used to show user-posted feedback on sets or collections.
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # Nested user details

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author']



# Serializes a flashcard set, including:
# - The set’s basic details (id, name, timestamps)
# - Nested 'cards' to display all flashcards in this set
# - Nested 'comments' to show feedback from users
# - The 'author' to identify who created this set
# Great for providing a complete overview of a set.
class FlashCardSetSerializer(serializers.ModelSerializer):
    cards = FlashCardSerializer(many=True, read_only=True)  # Remove source='cards'
    comments = CommentSerializer(many=True, read_only=True)  # Remove source='comments'
    author = UserSerializer(read_only=True)

    class Meta:
        model = FlashCardSet
        fields = ['id', 'name', 'createdAt', 'updatedAt', 'author', 'cards', 'comments']



# Serializes a collection which associates a single set with an author and a comment.
# - 'set' is a primary key field referencing a FlashCardSet
# - 'author' is nested to show who owns the collection
# Useful for showing how sets are grouped and annotated by a user.
class CollectionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'comment', 'author']
