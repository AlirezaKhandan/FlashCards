from rest_framework import serializers
from .models import FlashCardSet, FlashCard, Comment, Collection
from django.contrib.auth.models import User 



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
    author = UserSerializer(read_only=True) 

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author']




class FlashCardSetSerializer(serializers.ModelSerializer):
    cards = FlashCardSerializer(many=True, read_only=True)  
    comments = CommentSerializer(many=True, read_only=True)  
    author = UserSerializer(read_only=True)

    class Meta:
        model = FlashCardSet
        fields = ['id', 'name', 'createdAt', 'updatedAt', 'author', 'cards', 'comments']




class CollectionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'comment', 'author']
