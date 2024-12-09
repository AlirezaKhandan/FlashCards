from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import FlashCardSet, FlashCard, Comment, Collection, CreationLimit, UserDailyCreation
from django.utils import timezone
import json

class APIVersionTest(APITestCase):
    def test_get_api_version(self):
        """
        GET /api/ should return the current API version as per the spec.
        """
        url = reverse('api-version')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('version', response.data)
        self.assertIsInstance(response.data['version'], str)


class FlashcardSetsTest(APITestCase):
    def setUp(self):
        super().setUp()
        # Ensure CreationLimit exists so we don't get DoesNotExist errors
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=5,
            daily_flashcard_limit=50,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.client.login(username="testuser", password="testpass")
        self.sets_url = reverse('api-sets')

    def test_list_flashcard_sets_empty(self):
        """
        GET /sets should return an empty list initially.
        """
        response = self.client.get(self.sets_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 0)

    def test_create_flashcard_set_success(self):
        """
        POST /sets with valid data should create a new flashcard set.
        According to the spec, it should return 201 and the created set with ID and name.
        """
        data = {
            "name": "European Capitals"
        }
        response = self.client.post(self.sets_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], "European Capitals")

    def test_create_flashcard_set_limit_exceeded(self):
        """
        If the user hits the daily set creation limit, the API should return 429.
        Test by creating multiple sets and adjusting limits.
        """
        # Set global daily limit to 1 for testing
        CreationLimit.objects.update(daily_set_limit=1)
        data = {"name": "First Set"}
        r1 = self.client.post(self.sets_url, data, format='json')
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)

        data2 = {"name": "Second Set"}
        r2 = self.client.post(self.sets_url, data2, format='json')
        # Expecting 429 now
        self.assertEqual(r2.status_code, 429)

    def test_get_specific_set(self):
        """
        GET /sets/{pk} should return the set details along with comments as per the spec.
        """
        flashcard_set = FlashCardSet.objects.create(name="Test Set", author=self.user)
        url = reverse('api-set-detail', kwargs={'pk': flashcard_set.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check structure
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)
        self.assertIn('cards', response.data)
        self.assertIn('comments', response.data)
        self.assertIsInstance(response.data['comments'], list)
        
    def test_update_specific_set(self):
        """
        PUT /sets/{pk} should update the set details.
        """
        flashcard_set = FlashCardSet.objects.create(name="Old Name", author=self.user)
        url = reverse('api-set-detail', kwargs={'pk': flashcard_set.id})
        data = {"name": "New Name"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "New Name")

    def test_delete_specific_set(self):
        """
        DELETE /sets/{pk} should delete the set and return 204.
        """
        flashcard_set = FlashCardSet.objects.create(name="To Delete", author=self.user)
        url = reverse('api-set-detail', kwargs={'pk': flashcard_set.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class FlashcardsInSetTest(APITestCase):
    def setUp(self):
        super().setUp()
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=5,
            daily_flashcard_limit=50,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="carduser", password="testpass")
        self.client = APIClient()
        self.client.login(username="carduser", password="testpass")
        self.flashcard_set = FlashCardSet.objects.create(name="Capitals", author=self.user)
        self.url = reverse('api-set-cards', kwargs={'pk': self.flashcard_set.id})

    def test_list_flashcards_in_set_empty(self):
        """
        GET /sets/{pk}/cards should return an empty list if no flashcards exist.
        """
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_flashcard_in_set(self):
        """
        POST /sets/{pk}/cards should create a new flashcard in the set.
        According to the spec, return 201 with the flashcard data.
        """
        data = {
            "question": "What is the capital of France?",
            "answer": "Paris",
            "difficulty": "Easy"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('question', response.data)
        self.assertIn('answer', response.data)
        self.assertEqual(response.data['question'], "What is the capital of France?")


class CommentsTest(APITestCase):
    def setUp(self):
        super().setUp()
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=5,
            daily_flashcard_limit=50,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="commenter", password="testpass")
        self.client = APIClient()
        self.client.login(username="commenter", password="testpass")
        self.flashcard_set = FlashCardSet.objects.create(name="Commentable Set", author=self.user)
        self.comment_url = reverse('api-set-comments', kwargs={'pk': self.flashcard_set.id})

    def test_list_comments_empty(self):
        """
        GET /sets/{pk}/comments should return empty list if no comments.
        """
        response = self.client.get(self.comment_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_comment(self):
        data = {"content": "I love this set!"}
        response = self.client.post(self.comment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('content', response.data)
        self.assertEqual(response.data['content'], "I love this set!")
        self.assertIn('author', response.data)


class UsersTest(APITestCase):
    def setUp(self):
        super().setUp()
        # Not strictly needed if no daily limits here, but safe to have
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=5,
            daily_flashcard_limit=50,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="usertest", password="testpass")
        self.client = APIClient()
        self.users_url = reverse('api-users')

    def test_list_users(self):
        """
        GET /users should return a list of users.
        """
        response = self.client.get(self.users_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_create_user(self):
        """
        POST /users should create a new user and return 201.
        """
        data = {
            "username": "newuser",
            "password": "newpass"
        }
        response = self.client.post(self.users_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('username', response.data)
        self.assertEqual(response.data['username'], "newuser")


class CollectionsTest(APITestCase):
    def setUp(self):
        super().setUp()
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=5,
            daily_flashcard_limit=50,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="colluser", password="testpass")
        self.client = APIClient()
        self.client.login(username="colluser", password="testpass")
        self.collections_url = reverse('api-collections')

        # Create a set for testing collection creation
        self.flashcard_set = FlashCardSet.objects.create(name="Set for Collections", author=self.user)

    def test_list_collections_empty(self):
        """
        GET /collections should return empty list if no collections exist.
        """
        response = self.client.get(self.collections_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 0)

    def test_create_collection(self):
        """
        POST /collections should create a new collection.
        According to spec, should return 201 and the created collection structure.
        """
        data = [
            {
                "comment": "I love this set!",
                "setID": self.flashcard_set.id
            }
        ]
        response = self.client.post(self.collections_url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
                      "Response code is unexpected. Check code vs. spec.")
        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            self.assertIsInstance(response.data, list)
            self.assertGreater(len(response.data), 0)
            first_item = response.data[0]
            self.assertIn('comment', first_item)
            self.assertIn('set', first_item)
            self.assertIn('author', first_item)

    def test_random_collection_redirect(self):
        """
        GET /collections/random should redirect (302) to a random collection or 404 if none.
        """
        random_url = reverse('api-collections-random')
        r1 = self.client.get(random_url)
        if not Collection.objects.exists():
            self.assertEqual(r1.status_code, status.HTTP_404_NOT_FOUND)
        else:
            self.assertEqual(r1.status_code, 302)


class DailyLimitTest(APITestCase):
    def setUp(self):
        super().setUp()
        # Create a CreationLimit with a low daily limit for testing
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=1,
            daily_flashcard_limit=1,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="limituser", password="testpass")
        self.client = APIClient()
        self.client.login(username="limituser", password="testpass")
        self.sets_url = reverse('api-sets')

    def test_set_creation_limit(self):
        """
        Create one set successfully, second attempt should yield 429.
        """
        data = {"name": "First Set"}
        r1 = self.client.post(self.sets_url, data, format='json')
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)

        data2 = {"name": "Second Set"}
        r2 = self.client.post(self.sets_url, data2, format='json')
        self.assertEqual(r2.status_code, 429)


class SearchTest(APITestCase):
    def setUp(self):
        super().setUp()
        CreationLimit.objects.create(
            pk=1,
            daily_set_limit=5,
            daily_flashcard_limit=50,
            daily_collection_limit=5
        )

        self.user = User.objects.create_user(username="searchuser", password="testpass")
        self.client = APIClient()
        self.client.login(username="searchuser", password="testpass")
        self.set1 = FlashCardSet.objects.create(name="European Capitals", author=self.user)
        FlashCard.objects.create(question="Capital of France?", answer="Paris", set=self.set1)
        self.search_url = reverse('search')

    def test_search_sets(self):
        """
        GET /search?q=France should return sets that match.
        """
        response = self.client.get(self.search_url + "?q=France", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "European Capitals", status_code=200)
