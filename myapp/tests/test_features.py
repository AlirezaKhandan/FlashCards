import pytest
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from myapp.models import FlashCardSet, FlashCard, Comment, CreationLimit, UserFavorite, Tag, Rating, Collection
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
import json

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
       
        response = self.client.post(self.set_url, data, format='json')
        
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
        
        self.client.login(username="commenter2", password="testpass")
        data = {"content": "Updated comment text"}
        r = self.client.post(self.update_url, data, format='multipart')
        self.assertEqual(r.status_code, 302)  # Assuming a redirect on success
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated comment text")

    def test_update_another_users_comment(self):
        
        self.client.login(username="other", password="testpass2")
        data = {"content": "Should not update"}
        r = self.client.post(self.update_url, data, format='multipart')
        
        self.assertNotEqual(r.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Initial comment")

    def test_delete_own_comment(self):
        
        self.client.login(username="commenter2", password="testpass")
        r = self.client.post(self.delete_url, {}, format='multipart')
        self.assertEqual(r.status_code, 302)  
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_another_users_comment(self):
        self.client.login(username="other", password="testpass2")
        r = self.client.post(self.delete_url, {}, format='multipart')
        
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

class StudyModeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="studymode", password="testpass")
        self.client = Client()
        self.client.login(username="studymode", password="testpass")

        self.set_obj = FlashCardSet.objects.create(name="Capital Cities", author=self.user)
        FlashCard.objects.create(question="Capital of France?", answer="Paris", set=self.set_obj)
        FlashCard.objects.create(question="Capital of Japan?", answer="Tokyo", set=self.set_obj)

        self.study_url = reverse('study-mode', kwargs={'pk': self.set_obj.pk})

    def test_study_mode_access(self):
        """
        Ensure that a logged-in user can access study mode for a set they own.
        """
        response = self.client.get(self.study_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Study Mode:")
        
        self.assertIn('flashcards_json', response.context)

        flashcards_data = json.loads(response.context['flashcards_json'])
        self.assertEqual(len(flashcards_data), 2)
        self.assertEqual(flashcards_data[0]['answer'], "Paris")

    def test_study_mode_requires_login(self):
        """
        Check that if user is not logged in, they get redirected.
        """
        self.client.logout()
        response = self.client.get(self.study_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)  
class ToggleFavoriteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="favs", password="testpass")
        self.other_user = User.objects.create_user(username="other", password="otherpass")
        self.client = Client()
        self.client.login(username="favs", password="testpass")

        self.set_obj = FlashCardSet.objects.create(name="Geography", author=self.other_user)
        self.toggle_url = reverse('toggle-favorite')

    def test_toggle_favorite_set(self):
       
        response = self.client.post(self.toggle_url, 
            data=json.dumps({"type": "set", "id": self.set_obj.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn("favorited", response.json())
        self.assertTrue(response.json()["favorited"])
        self.assertTrue(UserFavorite.objects.filter(user=self.user, object_id=self.set_obj.id).exists())

      
        response = self.client.post(self.toggle_url, 
            data=json.dumps({"type": "set", "id": self.set_obj.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["favorited"])
        self.assertFalse(UserFavorite.objects.filter(user=self.user, object_id=self.set_obj.id).exists())

    def test_toggle_invalid_type(self):
        
        response = self.client.post(self.toggle_url, 
            data=json.dumps({"type": "collection", "id": self.set_obj.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

class UpdateCollectionSetsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="collector", password="testpass")
        self.client = Client()
        self.client.login(username="collector", password="testpass")

        self.set_obj1 = FlashCardSet.objects.create(name="Math Set", author=self.user)
        self.set_obj2 = FlashCardSet.objects.create(name="History Set", author=self.user)
        self.collection = Collection.objects.create(name="My Collection", author=self.user)
        self.update_url = reverse('collection-edit', kwargs={'pk': self.collection.pk})

    def test_update_collection_add_sets(self):
        
        
        self.assertEqual(self.collection.sets.count(), 0)

        
        response = self.client.post(self.update_url, {
            'name': 'My Updated Collection',
            'description': 'New Desc',
            'selected_sets': [str(self.set_obj1.id), str(self.set_obj2.id)]
        })
        self.assertRedirects(response, reverse('collection-list'))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.sets.count(), 2)
        self.assertIn(self.set_obj1, self.collection.sets.all())
        self.assertIn(self.set_obj2, self.collection.sets.all())

    def test_update_collection_remove_sets(self):
        
        self.collection.sets.add(self.set_obj1, self.set_obj2)
        self.assertEqual(self.collection.sets.count(), 2)

      
        response = self.client.post(self.update_url, {
            'name': 'No Sets',
            'description': 'Empty now'
            
        })
        self.assertRedirects(response, reverse('collection-list'))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.sets.count(), 0)

    def test_update_collection_own_sets_only(self):
        """
        Ensure that user cannot add sets they do not own.
        """
        other_user = User.objects.create_user(username="otheruser", password="otherpass")
        other_set = FlashCardSet.objects.create(name="Other Set", author=other_user)

        response = self.client.post(self.update_url, {
            'name': 'Try Adding Other Set',
            'description': 'Invalid attempt',
            'selected_sets': [str(other_set.id)]
        })
        
        self.assertRedirects(response, reverse('collection-list'))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.sets.count(), 0)  

class TagLimitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tagtester", password="testpass")
        self.client = Client()
        self.client.login(username="tagtester", password="testpass")
        self.url = reverse('flashcard-set-add')

    def test_set_creation_too_many_tags(self):
        """
        Creating a set with more than 8 tags should fail.
        """
        too_many_tags = ",".join([f"tag{i}" for i in range(10)])
        response = self.client.post(self.url, {
            'name': 'Tag Heavy Set',
            'tag_names': too_many_tags
        })
