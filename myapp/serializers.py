from rest_framework import serializers
from .models import FlashCardSet, FlashCard, Comment, Collection
from django.contrib.auth.models import User  # Use Django's default User model

class UserSerializer(serializers.ModelSerializer):
    admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'admin']

    def get_admin(self, obj):
        return obj.is_superuser

class FlashCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashCard
        fields = ['id', 'question', 'answer', 'difficulty']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # Nested user details

    class Meta:
        model = Comment
        fields = ['id', 'comment', 'author']

class FlashCardSetSerializer(serializers.ModelSerializer):
    cards = FlashCardSerializer(many=True, read_only=True)  # Remove source='cards'
    comments = CommentSerializer(many=True, read_only=True)  # Remove source='comments'
    author = UserSerializer(read_only=True)

    class Meta:
        model = FlashCardSet
        fields = ['id', 'name', 'createdAt', 'updatedAt', 'author', 'cards', 'comments']


class CollectionSerializer(serializers.ModelSerializer):
    set = serializers.PrimaryKeyRelatedField(queryset=FlashCardSet.objects.all())
    author = UserSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'comment', 'set', 'author']
