from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.IntegerField(write_only=True, default=User.CUSTOMER)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "confirm_password",
            "role",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "confirm_password": {"write_only": True},
        }

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords must match"}
            )
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop(
            "role", User.CUSTOMER
        )  # Default to CUSTOMER if not provided
        user = User(
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            username=validated_data["username"],
            email=validated_data["email"],
            role=role,
        )
        user.set_password(password)
        user.save()

        # Check if UserProfile already exists for this user
        if not hasattr(user, "userprofile"):
            UserProfile.objects.create(user=user)

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "profile_picture",
            "cover_photo",
            "address",
            "country",
            "state",
            "city",
            "pin_code",
            "latitude",
            "longitude",
        ]
        extra_kwargs = {
            "profile_picture": {"required": False},
            "cover_photo": {"required": False},
            "address": {"required": False},
            "country": {"required": False},
            "state": {"required": False},
            "city": {"required": False},
            "pin_code": {"required": False},
            "latitude": {"required": False},
            "longitude": {"required": False},
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source="userprofile", read_only=True)

    # Import VendorSerializer only inside this class to avoid circular import
    def get_vendor(self, obj):
        from vendor.serializers import \
            VendorSerializer  # Import here to avoid circular import

        if hasattr(obj, "vendor"):
            return VendorSerializer(obj.vendor).data
        return None

    vendor = serializers.SerializerMethodField("get_vendor")

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "role",
            "profile",
            "vendor",
        ]


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        token_key = data.get("token")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords must match"}
            )

        # Check if the user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist"}
            )

        # Validate the token
        try:
            token = Token.objects.get(key=token_key, user=user)
        except Token.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        return data

    def save(self):
        email = self.validated_data["email"]
        new_password = self.validated_data["new_password"]

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        return user
