import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from myapp.models import FlashCardSet, FlashCard, Comment, CreationLimit, UserFavorite, Tag, Rating, Collection
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase

@pytest.mark.django_db
class TestComments:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="commenter", password="testpass")
        self.client = APIClient()
        self.client.login(username="commenter", password="testpass")
        self.flashcard_set = FlashCardSet.objects.create(name="Commentable Set", author=self.user)
        self.comment_url = reverse('api-set-comments', kwargs={'pk': self.flashcard_set.id})

    def test_list_comments_empty(self):
        response = self.client.get(self.comment_url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_create_comment(self):
        data = {"content": "I love this set!"}
        response = self.client.post(self.comment_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'content' in response.data
        assert response.data['content'] == "I love this set!"
        assert 'author' in response.data


@pytest.mark.django_db
class TestFavorites:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="favtester", password="testpass")
        self.client = APIClient()
        self.client.login(username="favtester", password="testpass")

        self.set = FlashCardSet.objects.create(name="Fav Set", author=self.user)
        self.fav_url = reverse('api-add-favorite')

    def test_favorite_set(self):
        data = {"type": "set", "id": self.set.id}
        response = self.client.post(self.fav_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        fav_url = reverse('user-favourites')
        fav_page = self.client.get(fav_url)
        assert fav_page.status_code == 200
        assert "Fav Set" in str(fav_page.content)

    def test_favorite_already_favorited_set(self):
        data = {"type": "set", "id": self.set.id}
        self.client.post(self.fav_url, data, format='json')
        r2 = self.client.post(self.fav_url, data, format='json')
        assert r2.status_code == 400
        assert 'Already in favorites' in r2.data.get('error', '')


@pytest.mark.django_db
class TestTagValidation:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="tagtester", password="testpass")
        self.client = APIClient()
        self.client.login(username="tagtester", password="testpass")
        self.set_url = reverse('api-sets')

    def test_exceed_tag_limit_on_set_creation(self):
        data = {
            "name": "Tagged Set",
            "tag_names": ",".join([f"tag{i}" for i in range(10)])  # 10 tags
        }
        # This depends on if your API supports tag_names directly.
        # If not, this test might need adjusting or calling the update endpoint.
        # Expecting a validation error
        response = self.client.post(self.set_url, data, format='json')
        # If your code raises a validation error with 400:
        assert response.status_code in [400, 422]
        assert 'cannot have more than 8 tags' in str(response.content).lower()


@pytest.mark.django_db
class TestCommentUpdateDelete(APITestCase):
    def setUp(self):
        super().setUp()
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        # Author of the comment
        self.author_user = User.objects.create_user(username="commenter2", password="testpass")
        # Another user
        self.other_user = User.objects.create_user(username="other", password="testpass2")

        self.set_obj = FlashCardSet.objects.create(name="Commentable Set2", author=self.author_user)
        self.comment = Comment.objects.create(
            author=self.author_user,
            content="Initial comment",
            flashcard_set=self.set_obj
        )

        self.update_url = reverse('comment-edit', kwargs={'pk': self.comment.id})
        self.delete_url = reverse('comment-delete', kwargs={'pk': self.comment.id})

    def test_update_own_comment(self):
        # Log in as the author of the comment
        self.client.login(username="commenter2", password="testpass")
        data = {"content": "Updated comment text"}
        r = self.client.post(self.update_url, data, format='multipart')
        self.assertEqual(r.status_code, 302)  # Assuming a redirect on success
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated comment text")

    def test_update_another_users_comment(self):
        # Attempt to update comment as a different user (not author)
        self.client.login(username="other", password="testpass2")
        data = {"content": "Should not update"}
        r = self.client.post(self.update_url, data, format='multipart')
        # Expect a permission denial (likely 403), or no success redirect
        self.assertNotEqual(r.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Initial comment")

    def test_delete_own_comment(self):
        # Log in as the author of the comment
        self.client.login(username="commenter2", password="testpass")
        r = self.client.post(self.delete_url, {}, format='multipart')
        self.assertEqual(r.status_code, 302)  # Assuming a redirect on success
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_another_users_comment(self):
        self.client.login(username="other", password="testpass2")
        r = self.client.post(self.delete_url, {}, format='multipart')
        # Expect forbidden
        self.assertNotEqual(r.status_code, 302)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())



@pytest.mark.django_db
class TestRating:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="rater", password="testpass")
        self.client = APIClient()
        self.client.login(username="rater", password="testpass")
        self.set_obj = FlashCardSet.objects.create(name="Rateable Set", author=self.user)
        self.rate_url = reverse('rate-item')

    def test_rate_set(self):
        data = {
            "model": "flashcardset",
            "object_id": self.set_obj.id,
            "score": 4
        }
        r = self.client.post(self.rate_url, data)
        assert r.status_code == 200
        assert 'average_rating' in r.json()
        assert r.json()['average_rating'] == 4.0

        data["score"] = 5
        r2 = self.client.post(self.rate_url, data)
        assert r2.status_code == 200
        assert r2.json()['average_rating'] == 5.0


@pytest.mark.django_db
class TestUnauthorizedActions:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.owner = User.objects.create_user(username="owner", password="testpass")
        self.stranger = User.objects.create_user(username="stranger", password="testpass2")
        self.set_obj = FlashCardSet.objects.create(name="Private Set", author=self.owner)
        self.edit_url = reverse('api-set-detail', kwargs={'pk': self.set_obj.id})

    def test_stranger_cannot_edit_set(self):
        client = APIClient()
        client.login(username="stranger", password="testpass2")
        data = {"name": "Hacked Name"}
        r = client.put(self.edit_url, data, format='json')
        assert r.status_code == 403


@pytest.mark.django_db
class TestSearch:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="searchuser", password="testpass")
        self.client = APIClient()
        self.client.login(username="searchuser", password="testpass")
        self.set1 = FlashCardSet.objects.create(name="European Capitals", author=self.user)
        FlashCard.objects.create(question="Capital of France?", answer="Paris", set=self.set1)
        self.search_url = reverse('search')

    def test_search_sets(self):
        response = self.client.get(self.search_url + "?q=France", format='json')
        assert response.status_code == 200
        assert "European Capitals" in str(response.content)


@pytest.mark.django_db
class TestSearchByTags:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="tagsearch", password="testpass")
        self.client = APIClient()
        self.client.login(username="tagsearch", password="testpass")
        self.set_obj = FlashCardSet.objects.create(name="French Geography", author=self.user)
        tag1 = Tag.objects.create(name="geography")
        tag2 = Tag.objects.create(name="french")
        self.set_obj.tags.add(tag1, tag2)
        self.search_url = reverse('search')

    def test_search_by_tag(self):
        response = self.client.get(self.search_url + "?q=geography")
        assert response.status_code == 200
        assert "French Geography" in str(response.content)

        response2 = self.client.get(self.search_url + "?q=history")
        assert response2.status_code == 200
        assert "French Geography" not in str(response2.content)
