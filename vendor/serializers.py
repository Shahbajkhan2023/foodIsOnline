from rest_framework import serializers
from accounts.models import User, UserProfile
from .models import Vendor
from accounts.serializers import UserSerializer, UserProfileSerializer  # Adjust the import path based on your project structure


class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Display only, not editable
    user_profile = UserProfileSerializer(read_only=True)  # Display only, not editable

    class Meta:
        model = Vendor
        fields = [
            'id', 'user', 'user_profile', 'vendor_name', 'vendor_license', 'is_approved', 
            'created_at', 'modified_at'
        ]
