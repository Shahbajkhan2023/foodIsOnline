import factory
from django.contrib.auth import get_user_model

User = get_user_model()  


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = 'Test'
    last_name = 'User'
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'testpassword')  # Ensure this hashes the password
    is_active = True