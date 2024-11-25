from rest_framework import serializers
from .models import FlashCardSet, FlashCard, Comment, Collection, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'admin']


class FlashCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashCard
        fields = ['id', 'question', 'answer', 'difficulty']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer()  # Nested user details

    class Meta:
        model = Comment
        fields = ['id', 'comment', 'author']


class FlashCardSetSerializer(serializers.ModelSerializer):
    cards = FlashCardSerializer(many=True, read_only=True)  # Nested flashcards
    comments = CommentSerializer(many=True, read_only=True)  # Nested comments

    class Meta:
        model = FlashCardSet
        fields = ['id', 'name', 'createdAt', 'updatedAt', 'cards', 'comments']
