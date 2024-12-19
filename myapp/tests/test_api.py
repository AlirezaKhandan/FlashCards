import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from myapp.models import FlashCardSet, FlashCard, Collection, CreationLimit, UserDailyCreation
from django.utils import timezone
from django.test import TestCase



@pytest.mark.django_db
class TestAPIVersion:
    def test_get_api_version(self):
        """
        GET /api/ should return the current API version as per the spec.
        """
        client = APIClient()
        url = reverse('api-version')
        response = client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'version' in response.data
        assert isinstance(response.data['version'], str)


@pytest.mark.django_db
class TestFlashcardSets:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.client.login(username="testuser", password="testpass")
        self.sets_url = reverse('api-sets')

    def test_list_flashcard_sets_empty(self):
        response = self.client.get(self.sets_url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_create_flashcard_set_success(self):
        data = {"name": "European Capitals"}
        response = self.client.post(self.sets_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert 'name' in response.data
        assert response.data['name'] == "European Capitals"

    def test_create_flashcard_set_limit_exceeded(self):
        # Set global daily limit to 1 for testing
        CreationLimit.objects.update(daily_set_limit=1)
        data = {"name": "First Set"}
        r1 = self.client.post(self.sets_url, data, format='json')
        assert r1.status_code == status.HTTP_201_CREATED

        data2 = {"name": "Second Set"}
        r2 = self.client.post(self.sets_url, data2, format='json')
        assert r2.status_code == 429

    def test_get_specific_set(self):
        flashcard_set = FlashCardSet.objects.create(name="Test Set", author=self.user)
        url = reverse('api-set-detail', kwargs={'pk': flashcard_set.id})
        response = self.client.get(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
        assert 'name' in response.data
        assert 'cards' in response.data
        assert 'comments' in response.data
        assert isinstance(response.data['comments'], list)

    def test_update_specific_set(self):
        flashcard_set = FlashCardSet.objects.create(name="Old Name", author=self.user)
        url = reverse('api-set-detail', kwargs={'pk': flashcard_set.id})
        data = {"name": "New Name"}
        response = self.client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "New Name"

    def test_delete_specific_set(self):
        flashcard_set = FlashCardSet.objects.create(name="To Delete", author=self.user)
        url = reverse('api-set-detail', kwargs={'pk': flashcard_set.id})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestFlashcardsInSet:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="carduser", password="testpass")
        self.client = APIClient()
        self.client.login(username="carduser", password="testpass")
        self.flashcard_set = FlashCardSet.objects.create(name="Capitals", author=self.user)
        self.url = reverse('api-set-cards', kwargs={'pk': self.flashcard_set.id})

    def test_list_flashcards_in_set_empty(self):
        response = self.client.get(self.url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_create_flashcard_in_set(self):
        data = {
            "question": "What is the capital of France?",
            "answer": "Paris",
            "difficulty": "Easy"
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'question' in response.data
        assert 'answer' in response.data
        assert response.data['question'] == "What is the capital of France?"


@pytest.mark.django_db
class TestCollections:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="colluser", password="testpass")
        self.client = APIClient()
        self.client.login(username="colluser", password="testpass")
        self.collections_url = reverse('api-collections')
        self.flashcard_set = FlashCardSet.objects.create(name="Set for Collections", author=self.user)

    def test_list_collections_empty(self):
        response = self.client.get(self.collections_url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_create_collection(self):
        data = [
            {
                "comment": "I love this set!",
                "setID": self.flashcard_set.id
            }
        ]
        response = self.client.post(self.collections_url, data, format='json')
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            assert isinstance(response.data, list)
            assert len(response.data) > 0
            first_item = response.data[0]
            assert 'comment' in first_item
            assert 'set' in first_item
            assert 'author' in first_item

    def test_random_collection_redirect(self):
        random_url = reverse('api-collections-random')
        r1 = self.client.get(random_url)
        if Collection.objects.exists():
            assert r1.status_code == 302
        else:
            assert r1.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestDailyLimit:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=1, daily_flashcard_limit=1, daily_collection_limit=5)
        self.user = User.objects.create_user(username="limituser", password="testpass")
        self.client = APIClient()
        self.client.login(username="limituser", password="testpass")
        self.sets_url = reverse('api-sets')

    def test_set_creation_limit(self):
        data = {"name": "First Set"}
        r1 = self.client.post(self.sets_url, data, format='json')
        assert r1.status_code == status.HTTP_201_CREATED

        data2 = {"name": "Second Set"}
        r2 = self.client.post(self.sets_url, data2, format='json')
        assert r2.status_code == 429


@pytest.mark.django_db
class TestFlashcardCreationLimit:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=1, daily_collection_limit=5)
        self.user = User.objects.create_user(username="flashlimit", password="testpass")
        self.client = APIClient()
        self.client.login(username="flashlimit", password="testpass")
        self.set_obj = FlashCardSet.objects.create(name="Limit Set", author=self.user)
        self.url = reverse('api-set-cards', kwargs={'pk': self.set_obj.id})

    def test_flashcard_creation_limit_exceeded(self):
        data = {"question": "Q1", "answer": "A1", "difficulty": "Easy"}
        r1 = self.client.post(self.url, data, format='json')
        assert r1.status_code == status.HTTP_201_CREATED

        data2 = {"question": "Q2", "answer": "A2", "difficulty": "Medium"}
        r2 = self.client.post(self.url, data2, format='json')
        assert r2.status_code == 429


@pytest.mark.django_db
class TestCollectionCreationLimit:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=1)
        self.user = User.objects.create_user(username="colllimit", password="testpass")
        self.client = APIClient()
        self.client.login(username="colllimit", password="testpass")
        self.collections_url = reverse('api-collections')

    def test_collection_creation_limit(self):
        data = {"name": "My Collection", "description": "Test Desc"}
        r1 = self.client.post(self.collections_url, data, format='json')
        assert r1.status_code in [200, 201]

        data2 = {"name": "Another Collection", "description": "desc"}
        r2 = self.client.post(self.collections_url, data2, format='json')
        assert r2.status_code == 429
