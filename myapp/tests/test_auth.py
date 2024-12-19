import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from myapp.models import CreationLimit


@pytest.mark.django_db
class TestUserEndpoints:
    def setup_method(self):
        CreationLimit.objects.create(pk=1, daily_set_limit=5, daily_flashcard_limit=50, daily_collection_limit=5)
        self.user = User.objects.create_user(username="usertest", password="testpass")
        self.client = APIClient()
        self.users_url = reverse('api-users')

    def test_list_users(self):
        """
        GET /users should return a list of users.
        """
        response = self.client.get(self.users_url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_create_user(self):
        """
        POST /users should create a new user and return 201.
        """
        data = {
            "username": "newuser",
            "password": "newpass"
        }
        response = self.client.post(self.users_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert 'username' in response.data
        assert response.data['username'] == "newuser"
