from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import FlashCardSet, FlashCard, Comment
from .serializers import FlashCardSetSerializer, FlashCardSerializer, CommentSerializer

# Core default view
def mypage(request):
    return render(request, 'index.html')


# Version API
@api_view(['GET'])
def version(request):
    return Response({"version": "1.0.0"})


# FlashCardSet List and Create API
class FlashCardSetList(APIView):
    def get(self, request):
        flashcard_sets = FlashCardSet.objects.all()
        serializer = FlashCardSetSerializer(flashcard_sets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FlashCardSetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# FlashCardSet Retrieve, Update, Delete API
class FlashCardSetDetail(APIView):
    def get(self, request, pk):
        flashcard_set = get_object_or_404(FlashCardSet, pk=pk)
        serializer = FlashCardSetSerializer(flashcard_set)
        return Response(serializer.data)

    def put(self, request, pk):
        flashcard_set = get_object_or_404(FlashCardSet, pk=pk)
        serializer = FlashCardSetSerializer(flashcard_set, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        flashcard_set = get_object_or_404(FlashCardSet, pk=pk)
        flashcard_set.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# FlashCard List and Add API
class FlashCardList(APIView):
    def get(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id)
        flashcards = FlashCard.objects.filter(set=flashcard_set)
        serializer = FlashCardSerializer(flashcards, many=True)
        return Response(serializer.data)

    def post(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id)
        data = request.data
        data['set'] = set_id
        serializer = FlashCardSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Comment Add API
class CommentCreate(APIView):
    def post(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id)
        data = request.data
        data['flashcard_set'] = set_id
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Comment List API
class CommentList(APIView):
    def get(self, request, set_id):
        flashcard_set = get_object_or_404(FlashCardSet, pk=set_id)
        comments = Comment.objects.filter(flashcard_set=flashcard_set)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)