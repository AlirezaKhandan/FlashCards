from django.test import TestCase
from django.contrib.auth.models import User
from .models import FlashCardSet, FlashCard

class DailyLimitTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_flashcard_set_limit(self):
        self.client.login(username="testuser", password="password123")
        for _ in range(5):
            response = self.client.post('/sets/add/', {'name': f'Set {_}'})
            self.assertEqual(response.status_code, 200)  # Should succeed
        response = self.client.post('/sets/add/', {'name': 'Extra Set'})
        self.assertEqual(response.status_code, 429)  # Should fail after 5 sets

    def test_flashcard_limit(self):
        self.client.login(username="testuser", password="password123")
        set = FlashCardSet.objects.create(name="Sample Set", author=self.user)
        for _ in range(50):
            response = self.client.post(f'/sets/{set.id}/cards/add/', {
                'question': f'Question {_}',
                'answer': f'Answer {_}',
                'difficulty': 'Easy'
            })
            self.assertEqual(response.status_code, 200)  # Should succeed
        response = self.client.post(f'/sets/{set.id}/cards/add/', {
            'question': 'Extra Question',
            'answer': 'Extra Answer',
            'difficulty': 'Easy'
        })
        self.assertEqual(response.status_code, 429)  # Should fail after 50 cards
