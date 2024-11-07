import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.messages import get_messages
from django.test import Client

User = get_user_model()

@pytest.mark.django_db
def test_login_view_authenticated(client):
    user = get_user_model().objects.create_user(
        first_name="Test",
        last_name="User",
        username="testuser",  
        email="testuser@example.com",
        password="password123"
    )
    user.is_active = True  
    user.set_password("password123")  
    user.save()  

    logged_in = client.login(email="testuser@example.com", password="password123")
    assert logged_in, "Failed to log in" 

    
    response = client.get('/login/') 

    assert response.status_code == 302
    assert response.url == reverse("myAccount")

    
@pytest.mark.django_db
def test_login_view_valid_login(client):
    
    user = get_user_model().objects.create_user(
        first_name="Test",
        last_name="User",
        username="testuser",  
        email="testuser@example.com",
        password="password123"
    )
    user.is_active = True  
    user.set_password("password123")  
    user.save()

    response = client.post(reverse("login"), {
        "email": "testuser@example.com",
        "password": "password123"
    })

    assert response.status_code == 302
    assert response.url == reverse("home")

@pytest.mark.django_db
def test_login_view_invalid_login(client):
    
    user = get_user_model().objects.create_user(
        first_name="Test",
        last_name="User",
        username="testuser",  
        email="testuser@example.com",
        password="password123"
    )
    user.is_active = True  
    user.set_password("password123")  
    user.save()

    response = client.post(reverse("login"), {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 302
    assert response.url == reverse("login")