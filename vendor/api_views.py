from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserUpdateSerializer


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user  # Get the authenticated user

    # Initialize the serializer with the user instance and request data
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        # Save the updated user instance
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)