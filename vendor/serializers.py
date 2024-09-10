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


class UserUpdateSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(write_only=True, required=False, allow_null=True)
    cover_photo = serializers.ImageField(write_only=True, required=False, allow_null=True)
    vendor_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vendor_license = serializers.ImageField(write_only=True, required=False, allow_null=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    country = serializers.CharField(write_only=True, required=False, allow_blank=True)
    state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pin_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    latitude = serializers.CharField(write_only=True, required=False, allow_blank=True)
    longitude = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'phone_number',
            'profile_picture', 'cover_photo', 'vendor_name', 'vendor_license',
            'address', 'country', 'state', 'city',
            'pin_code', 'latitude', 'longitude'
        ]

    def update(self, instance, validated_data):
        # User fields update karein
        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        # UserProfile handle karein
        user_profile_data = {
            'profile_picture': validated_data.get('profile_picture'),
            'cover_photo': validated_data.get('cover_photo'),
            'address': validated_data.get('address'),
            'country': validated_data.get('country'),
            'state': validated_data.get('state'),
            'city': validated_data.get('city'),
            'pin_code': validated_data.get('pin_code'),
            'latitude': validated_data.get('latitude'),
            'longitude': validated_data.get('longitude')
        }

        # UserProfile ko get ya create karein
        user_profile, created = UserProfile.objects.get_or_create(user=instance)
        for attr, value in user_profile_data.items():
            if value is not None:  # None values ko skip karein
                setattr(user_profile, attr, value)
        user_profile.save()

        # Vendor handle karein
        vendor_data = {
            'vendor_name': validated_data.get('vendor_name'),
            'vendor_license': validated_data.get('vendor_license')
        }

        # Existing Vendor ko update karein ya naya create karein
        if vendor_data.get('vendor_name') or vendor_data.get('vendor_license'):
            vendor, created = Vendor.objects.update_or_create(
                user=instance,
                defaults={
                    'user_profile': user_profile,
                    'vendor_name': vendor_data.get('vendor_name'),
                    'vendor_license': vendor_data.get('vendor_license'),
                }
            )
            if not created:
                # Only non-null fields ko update karein
                for attr, value in vendor_data.items():
                    if value is not None:
                        setattr(vendor, attr, value)
                vendor.save()

        instance.save()
        return instance