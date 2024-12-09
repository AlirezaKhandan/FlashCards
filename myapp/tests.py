from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import FlashCardSet, FlashCard, Comment, Collection
from rest_framework.test import APIClient
from rest_framework import status

class DailyCreationLimitTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_flashcard_set_limit(self):
        # This test checks that after creating 5 sets, the user should get a 429 status
        # on the attempt to create the 6th set, matching our daily creation limit logic.
        self.client.login(username="testuser", password="password123")
        for _ in range(5):
            response = self.client.post('/sets/add/', {'name': f'Set {_}'})
            # Should redirect (302) on successful creation within limit
            self.assertEqual(response.status_code, 302)
        response = self.client.post('/sets/add/', {'name': 'Extra Set'})
        # After hitting limit, we expect a 429 Too Many Requests response.
        self.assertEqual(response.status_code, 429)

    def test_flashcard_limit(self):
        # Similar test for flashcards: create 50 flashcards successfully (302),
        # and the 51st should return 429.
        self.client.login(username="testuser", password="password123")
        flashcard_set = FlashCardSet.objects.create(name="Sample Set", author=self.user)
        for _ in range(50):
            response = self.client.post(f'/sets/{flashcard_set.id}/cards/add/', {
                'question': f'Question {_}',
                'answer': f'Answer {_}',
                'difficulty': 'Easy'
            })
            self.assertEqual(response.status_code, 302)
        # 51st flashcard exceeds the daily limit
        response = self.client.post(f'/sets/{flashcard_set.id}/cards/add/', {
            'question': 'Extra Question',
            'answer': 'Extra Answer',
            'difficulty': 'Easy'
        })
        self.assertEqual(response.status_code, 429)


class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123'
        })
        # Registration should redirect to success page
        self.assertEqual(response.status_code, 302)
        # Check user created
        self.assertTrue(User.objects.filter(username='newuser').exists())


class UserLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'testuser'
        self.password = 'password123'
        User.objects.create_user(username=self.username, password=self.password)

    def test_user_login(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
        # Successful login should redirect
        self.assertEqual(response.status_code, 302)
        # Check authentication in session
        self.assertIn('_auth_user_id', self.client.session)


class FlashCardSetCreationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_login(self.user)

    def test_flashcard_set_creation_within_limit(self):
        # Within daily set limit (5 sets)
        for i in range(5):
            response = self.client.post(reverse('flashcard-set-add'), {'name': f'Set {i}'})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(FlashCardSet.objects.filter(name=f'Set {i}', author=self.user).exists())

    def test_flashcard_set_creation_exceeding_limit(self):
        # Exceed daily set limit
        for i in range(5):
            self.client.post(reverse('flashcard-set-add'), {'name': f'Set {i}'})
        response = self.client.post(reverse('flashcard-set-add'), {'name': 'Extra Set'})
        self.assertEqual(response.status_code, 429)
        self.assertFalse(FlashCardSet.objects.filter(name='Extra Set', author=self.user).exists())


class FlashCardSetDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='Sample Set', author=self.user)

    def test_flashcard_set_detail_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('flashcard-set-detail', args=[self.flashcard_set.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sample Set')


class FlashCardSetUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='author', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='Original Name', author=self.author)

    def test_author_can_update_set(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('flashcard-set-edit', args=[self.flashcard_set.pk]), {
            'name': 'Updated Name'
        })
        self.assertEqual(response.status_code, 302)
        self.flashcard_set.refresh_from_db()
        self.assertEqual(self.flashcard_set.name, 'Updated Name')

    def test_other_user_cannot_update_set(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('flashcard-set-edit', args=[self.flashcard_set.pk]), {
            'name': 'Hacked Name'
        })
        # If unauthorized, returns 404 according to our get_queryset checks
        self.assertEqual(response.status_code, 404)
        self.flashcard_set.refresh_from_db()
        self.assertEqual(self.flashcard_set.name, 'Original Name')


class FlashCardSetDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='author', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='Set to Delete', author=self.author)

    def test_author_can_delete_set(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('flashcard-set-delete', args=[self.flashcard_set.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FlashCardSet.objects.filter(pk=self.flashcard_set.pk).exists())

    def test_other_user_cannot_delete_set(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('flashcard-set-delete', args=[self.flashcard_set.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(FlashCardSet.objects.filter(pk=self.flashcard_set.pk).exists())


class FlashCardCreationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='Test Set', author=self.user)
        self.client.force_login(self.user)

    def test_flashcard_creation_within_limit(self):
        # Create up to 50 flashcards successfully
        for i in range(50):
            response = self.client.post(reverse('flashcard-add', args=[self.flashcard_set.pk]), {
                'question': f'Question {i}',
                'answer': f'Answer {i}',
                'difficulty': 'Easy'
            })
            self.assertEqual(response.status_code, 302)
            self.assertTrue(FlashCard.objects.filter(question=f'Question {i}', set=self.flashcard_set).exists())

    def test_flashcard_creation_exceeding_limit(self):
        # After 50 flashcards, the 51st should fail with 429
        for i in range(50):
            self.client.post(reverse('flashcard-add', args=[self.flashcard_set.pk]), {
                'question': f'Question {i}',
                'answer': f'Answer {i}',
                'difficulty': 'Easy'
            })
        response = self.client.post(reverse('flashcard-add', args=[self.flashcard_set.pk]), {
            'question': 'Extra Question',
            'answer': 'Extra Answer',
            'difficulty': 'Easy'
        })
        self.assertEqual(response.status_code, 429)
        self.assertFalse(FlashCard.objects.filter(question='Extra Question', set=self.flashcard_set).exists())


class CommentCreationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='commenter', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='Commented Set', author=self.user)
        self.client.force_login(self.user)

    def test_comment_creation(self):
        response = self.client.post(reverse('comment-add', args=[self.flashcard_set.pk]), {
            'comment': 'Great set!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(comment='Great set!', flashcard_set=self.flashcard_set).exists())


class CollectionManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='collector', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='Collectible Set', author=self.user)
        self.client.force_login(self.user)

    def test_add_set_to_collection(self):
        response = self.client.post(reverse('collection-add', args=[self.flashcard_set.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Collection.objects.filter(author=self.user, set=self.flashcard_set).exists())

    def test_delete_set_from_collection(self):
        # First add the set to a collection
        collection = Collection.objects.create(author=self.user, set=self.flashcard_set)
        response = self.client.post(reverse('collection-delete', args=[collection.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Collection.objects.filter(pk=collection.pk).exists())


class SearchFunctionalityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='searcher', password='password123')
        self.flashcard_set1 = FlashCardSet.objects.create(name='Django Basics', author=self.user)
        self.flashcard_set2 = FlashCardSet.objects.create(name='Python Advanced', author=self.user)
        self.client.force_login(self.user)

    def test_search_flashcard_sets(self):
        response = self.client.get(reverse('search') + '?q=Django')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Basics')
        self.assertNotContains(response, 'Python Advanced')


class FlashCardSetAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_create_flashcard_set_api_within_limit(self):
        # Create 5 sets via API successfully
        for i in range(5):
            response = self.client.post(reverse('api-sets'), {'name': f'Set {i}'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(FlashCardSet.objects.filter(name=f'Set {i}', author=self.user).exists())

    def test_create_flashcard_set_api_exceeding_limit(self):
        # Exceeding daily limit should return 429
        for i in range(5):
            self.client.post(reverse('api-sets'), {'name': f'Set {i}'}, format='json')
        response = self.client.post(reverse('api-sets'), {'name': 'Extra Set'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(FlashCardSet.objects.filter(name='Extra Set', author=self.user).exists())


class FlashCardAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='API Set', author=self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_flashcard_api_within_limit(self):
        # Create up to 50 flashcards via API
        for i in range(50):
            response = self.client.post(reverse('api-set-cards', args=[self.flashcard_set.pk]), {
                'question': f'Question {i}',
                'answer': f'Answer {i}',
                'difficulty': 'Easy'
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(FlashCard.objects.filter(question=f'Question {i}', set=self.flashcard_set).exists())

    def test_create_flashcard_api_exceeding_limit(self):
        # 51st flashcard should return 429
        for i in range(50):
            self.client.post(reverse('api-set-cards', args=[self.flashcard_set.pk]), {
                'question': f'Question {i}',
                'answer': f'Answer {i}',
                'difficulty': 'Easy'
            }, format='json')
        response = self.client.post(reverse('api-set-cards', args=[self.flashcard_set.pk]), {
            'question': 'Extra Question',
            'answer': 'Extra Answer',
            'difficulty': 'Easy'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(FlashCard.objects.filter(question='Extra Question', set=self.flashcard_set).exists())


class UserAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_api(self):
        response = self.client.post(reverse('api-users'), {
            'username': 'apiuser',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='apiuser').exists())

    def test_get_user_api(self):
        user = User.objects.create_user(username='apiuser', password='password123')
        response = self.client.get(reverse('api-user-detail', args=[user.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'apiuser')


class CollectionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='password123')
        self.flashcard_set = FlashCardSet.objects.create(name='API Collection Set', author=self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_collection_api(self):
        response = self.client.post(reverse('api-collections'), {
            'set': self.flashcard_set.pk,
            'comment': 'My favorite set!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Collection.objects.filter(author=self.user, set=self.flashcard_set).exists())

    def test_get_collections_api(self):
        Collection.objects.create(author=self.user, set=self.flashcard_set, comment='Test Collection')
        response = self.client.get(reverse('api-user-collections', args=[self.user.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['comment'], 'Test Collection')
