from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from .models import User, UserProfile
from vendor.serializers import VendorSerializer
from vendor.models import Vendor


class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User and profile created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterVendorView(APIView):
    def post(self, request, *args, **kwargs):
        # Separate the data and files
        data = request.data.copy()  # Make a copy of the data to prevent mutation
        files = request.FILES  # Get the files

        # Initialize the serializers
        user_serializer = UserSerializer(data=data)
        vendor_serializer = VendorSerializer(data=data, context={'request': request})

        # Check if both serializers are valid
        if user_serializer.is_valid():
            # Save the user
            user = user_serializer.save()
            user.role = User.VENDOR
            user.save()
        else:
            # Return user serializer errors if not valid
            return Response({'user_errors': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure vendor serializer is valid
        if vendor_serializer.is_valid():
            # Create vendor instance
            vendor_data = vendor_serializer.validated_data
            vendor = Vendor(
                user=user,
                user_profile=UserProfile.objects.get_or_create(user=user)[0],
                vendor_name=vendor_data.get('vendor_name'),
                vendor_license=files.get('vendor_license'),  # Handle file upload
                is_approved=vendor_data.get('is_approved', False)
            )
            vendor.save()

            return Response({'message': 'Your account has been registered successfully! Please wait for the approval.'}, status=status.HTTP_201_CREATED)
        else:
            # Return vendor serializer errors if not valid
            return Response({'vendor_errors': vendor_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)