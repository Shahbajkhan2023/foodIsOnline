from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.authtoken.models import Token
from django.test import TestCase
from accounts.models import UserProfile
from vendor.models import Vendor
from accounts.api_views import PasswordResetView

from django.contrib.staticfiles.testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from accounts.models import User
from .factories import UserFactory
from rest_framework.authtoken.models import Token


User = get_user_model()


class HomeViewLiveServerTest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Chrome()
        cls.selenium.implicitly_wait(10)
        cls.ngrok_url = "https://8c5d-2405-201-3027-e01e-c3e2-5792-37da-6aa2.ngrok-free.app"  

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        
        active_user = User.objects.create(
            email="activel_vendor@example.com", 
            is_active=True, 
            role=User.VENDOR
        )
        inactive_user = User.objects.create(
            email="inactivel_vendor@example.com", 
            is_active=False, 
            role=User.VENDOR
        )

        self.vendor1 = Vendor.objects.create(
            vendor_name="Approved Active Vendor 1",
            is_approved=True,
            user=active_user
        )
        self.vendor2 = Vendor.objects.create(
            vendor_name="Unapproved Vendor",
            is_approved=False,
            user=active_user
        )
        self.vendor3 = Vendor.objects.create(
            vendor_name="Inactive Vendor",
            is_approved=True,
            user=inactive_user
        )

    def test_home_view_displays_approved_and_active_vendors(self):
        url = f"{self.ngrok_url}{reverse('home')}"
        self.selenium.get(url)

        vendor_elements = self.selenium.find_elements(By.CSS_SELECTOR, ".post-title h5 a")

        displayed_vendors = [vendor.text for vendor in vendor_elements]

        self.assertIn("Approved Active Vendor 1", displayed_vendors)
        self.assertNotIn("Unapproved Vendor", displayed_vendors)
        self.assertNotIn("Inactive Vendor", displayed_vendors)


class RegisterUserViewTest(APITestCase):
    def setUp(self):
        self.register_url = reverse('register_user') 
        self.valid_payload = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "role": User.CUSTOMER
        }
        self.invalid_payload = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "password": "password123",
            "confirm_password": "password456",  
            "role": User.CUSTOMER
        }

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "User and profile created successfully!")
        # Check that user was created
        self.assertTrue(User.objects.filter(username=self.valid_payload['username']).exists())

    def test_register_user_password_mismatch(self):
        response = self.client.post(self.register_url, self.invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)
        self.assertEqual(response.data["confirm_password"][0], "Passwords must match")

    def test_register_user_missing_field(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload.pop("username")  
        response = self.client.post(self.register_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        

class UserDetailViewTests(APITestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            first_name='John',
            last_name='Doe',
            username='john_doe',
            email='customer@example.com',
            password='password123',
        )
        self.customer.role = User.CUSTOMER  
        self.customer.is_active = True
        self.customer.save()

        self.vendor_user = User.objects.create_user(
            first_name='Jane',
            last_name='Doe',
            username='jane_doe',
            email='vendor@example.com',
            password='password123',
        )
        self.vendor_user.role = User.VENDOR  
        self.vendor_user.is_active = True
        self.vendor_user.save()

        
        self.vendor_user_profile, _ = UserProfile.objects.get_or_create(user=self.vendor_user) 
        
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            user_profile=self.vendor_user_profile,  
            vendor_name='Vendor Name',
            vendor_slug='vendor-name',
            vendor_license=None,  
            is_approved=True
        )
        
        self.url = reverse('user-details')  
 

    def test_user_detail_view_customer(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertNotIn('vendor', response.data)

    def test_user_detail_view_vendor(self):
        self.client.force_authenticate(user=self.vendor_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('vendor', response.data)

    def test_user_detail_view_unauthenticated(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_user_detail_view_vendor_not_found(self):
        self.vendor.delete()
        self.client.force_authenticate(user=self.vendor_user)
        
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "Vendor details not found.")



class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            first_name='john',
            last_name='doe',
            username='john_doe',
            email='testuser@example.com',
            password='old_password'
        )
        self.token = Token.objects.create(user=self.user)

    def test_password_reset_success(self):
         data = {
            'email': self.user.email,
            'token': self.token.key,
            'new_password': 'new_password',
            'confirm_password': 'new_password',
        }
         # Create a request using APIRequestFactory
         request = self.factory.post(reverse('password_reset'), data, format='json')
         view = PasswordResetView.as_view()
         

         # Call the view
         response = view(request)

         self.assertEqual(response.status_code, status.HTTP_200_OK)
         self.assertEqual(response.data, {"success": "Password has been reset successfully."})

         self.user.refresh_from_db()
         self.assertEqual(response.data, {"success": "Password has been reset successfully."})

    def test_password_reset_invalid_token(self):
        data = {
            'email': self.user.email,
            'token': 'invalid_token',
            'new_password': 'new_password',
            'confirm_password': 'new_password',
        }

        request = self.factory.post(reverse('password_reset'), data, format='json')
        view = PasswordResetView.as_view()
        
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["token"][0]), "Invalid or expired token")

    def test_password_reset_passwords_do_not_match(self):
        data = {
            'email': self.user.email,
            'token': self.token.key,
            'new_password': 'new_password',
            'confirm_password': 'different_password',
        }

        request = self.factory.post(reverse('password_reset'), data, format='json')
        view = PasswordResetView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['confirm_password'][0]), "Passwords must match")

    def test_password_reset_user_not_found(self):
        data = {
            'email': 'nonexisting@example.com',
            'token': self.token.key,
            'new_password': 'new_password',
            'confirm_password': 'new_password',
        }

        request = self.factory.post(reverse('password_reset'), data, format='json')
        view = PasswordResetView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "User with this email does not exist")
        

class RegisterVendorViewTestCase(APITransactionTestCase):
    def setUp(self):  # Corrected the method name to setUp
        self.url = reverse('register_vendor')

        self.valid_user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "john@example.com",
            "password": "securepassword",
            "confirm_password": "securepassword",
            "role": User.VENDOR,
        }

        self.valid_vendor_data = {
            "vendor_name": "John's Store",
            "vendor_license": None,  
            "is_approved": False,
        }

    def test_register_vendor_success(self):
        
        data = {**self.valid_user_data, **self.valid_vendor_data}
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)

        user = User.objects.get(username='johndoe')
        vendor = Vendor.objects.get(user=user)
        self.assertEqual(vendor.vendor_name, "John's Store")

    def test_register_vendor_invalid_user_data(self):
    
        invalid_data = {**self.valid_user_data, "username": ""}
        response = self.client.post(self.url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_errors", response.data)

    def test_register_vendor_invalid_vendor_data(self):
        # Invalid vendor name
        data = {**self.valid_user_data, **self.valid_vendor_data, "vendor_name": ""}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vendor_errors", response.data)

    def test_register_vendor_password_mismatch(self):
        # Password and confirm_password do not match
        invalid_data = {
            **self.valid_user_data,
            "confirm_password": "differentpassword"
        }
        response = self.client.post(self.url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)


class LoginViewTestCase(APITestCase):
    def setUp(self):
        self.user_password = "testpassword"
        self.user = UserFactory(email="testuser@example.com", password=self.user_password)
        self.login_url = reverse("api_login")  

    def test_login_success(self):
        data = {
            "email": self.user.email,
            "password": self.user_password,
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_failure_wrong_password(self):
        data = {
            "email": self.user.email,
            "password": "wrongpassword",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_login_failure_nonexistent_user(self):
        data = {
            "email": "nonexistent@example.com",
            "password": "testpassword",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
