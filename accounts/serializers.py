from rest_framework import serializers
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.IntegerField(write_only=True, default=User.CUSTOMER)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'password', 
            'confirm_password', 'role'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords must match"})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role', User.CUSTOMER)  # Default to CUSTOMER if not provided
        user = User(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data['email'],
            role=role
        )
        user.set_password(password)
        user.save()

        # Check if UserProfile already exists for this user
        if not hasattr(user, 'userprofile'):
            UserProfile.objects.create(user=user)

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'cover_photo', 'address_line_1', 'address_line_2',
            'country', 'state', 'city', 'pin_code', 'latitude', 'longitude'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False},
            'cover_photo': {'required': False},
            'address_line_1': {'required': False},
            'address_line_2': {'required': False},
            'country': {'required': False},
            'state': {'required': False},
            'city': {'required': False},
            'pin_code': {'required': False},
            'latitude': {'required': False},
            'longitude': {'required': False},
        }
