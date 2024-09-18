from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from vendor.models import Vendor
from vendor.serializers import VendorSerializer

from .models import User, UserProfile
from .serializers import (LoginSerializer, PasswordResetSerializer,
                          UserDetailSerializer, UserSerializer)


class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User and profile created successfully!"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterVendorView(APIView):
    def post(self, request, *args, **kwargs):
        # Separate the data and files
        data = request.data.copy()  # Make a copy of the data to prevent mutation
        files = request.FILES  # Get the files

        # Initialize the serializers
        user_serializer = UserSerializer(data=data)
        vendor_serializer = VendorSerializer(data=data, context={"request": request})

        # Check if both serializers are valid
        if user_serializer.is_valid():
            # Save the user
            user = user_serializer.save()
            user.role = User.VENDOR
            user.save()
        else:
            # Return user serializer errors if not valid
            return Response(
                {"user_errors": user_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure vendor serializer is valid
        if vendor_serializer.is_valid():
            # Create vendor instance
            vendor_data = vendor_serializer.validated_data
            vendor = Vendor(
                user=user,
                user_profile=UserProfile.objects.get_or_create(user=user)[0],
                vendor_name=vendor_data.get("vendor_name"),
                vendor_license=files.get("vendor_license"),  # Handle file upload
                is_approved=vendor_data.get("is_approved", False),
            )
            vendor.save()

            return Response(
                {
                    "message": "Your account has been registered successfully! Please wait for the approval."
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            # Return vendor serializer errors if not valid
            return Response(
                {"vendor_errors": vendor_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            user = authenticate(email=email, password=password)

            if user is not None:
                auth_login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Invalid login credentials"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()  # Delete the current user's token
        auth_logout(request)
        return Response({"message": "You are logged out."}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Use UserDetailSerializer to get complete user details
        serializer = UserDetailSerializer(user)

        # Filter details based on user role
        if user.role == User.VENDOR:
            # Return vendor-specific information
            vendor = Vendor.objects.filter(user=user).first()
            if vendor:
                vendor_serializer = VendorSerializer(vendor)
                return Response(
                    {"user": serializer.data, "vendor": vendor_serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                raise PermissionDenied("Vendor details not found.")

        elif user.role == User.CUSTOMER:
            # Return customer-specific information
            return Response({"user": serializer.data}, status=status.HTTP_200_OK)

        else:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)


class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"success": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
