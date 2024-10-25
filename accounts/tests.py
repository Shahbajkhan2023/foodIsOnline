from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User  


class RegisterUserViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('register_user')  

        self.valid_payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "first_name": "Test",
        "last_name": "User",
        "confirm_password": "strongpassword123"
        }
        self.invalid_payload = {
            "username": "",  
            "email": "invalid-email",  
            "password": "123",  
            "first_name": "",  
            "last_name": "",  
            "confirm_password": ""  
        }

    def test_create_user_success(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User and profile created successfully!")
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_create_user_invalid_data(self):
        response = self.client.post(self.url, self.invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)

