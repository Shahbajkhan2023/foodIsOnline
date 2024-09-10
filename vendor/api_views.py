from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .drf_custome_permission.permissions import IsVendor
from menu.models import Category, FoodItem
from menu.serializers import CategorySerializer, FoodItemSerializer
from .models import Vendor
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from .serializers import UserUpdateSerializer


class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    def put(self, request):
        user = request.user  # Get the authenticated user

        # Initialize the serializer with the user instance and request data
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            # Save the updated user instance
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VendorFoodItemsByCategoryView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsVendor]

    def get_vendor(self, user):
        # Retrieve the Vendor instance for the given user
        try:
            return Vendor.objects.get(user=user)
        except Vendor.DoesNotExist:
            raise ValueError("Vendor not found")

    def get(self, request, format=None):
        # List categories and their food items
        try:
            vendor = self.get_vendor(request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        categories = Category.objects.filter(vendor=vendor)
        category_data = []
        for category in categories:
            fooditems = FoodItem.objects.filter(vendor=vendor, category=category)
            fooditem_data = FoodItemSerializer(fooditems, many=True).data
            category_data.append({
                'category': CategorySerializer(category).data,
                'fooditems': fooditem_data
            })

        return Response(category_data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        # Add a new category
        try:
            vendor = self.get_vendor(request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        category_name = data.get('category_name')
        data['slug'] = slugify(category_name)

        serializer = CategorySerializer(data=data)
        if serializer.is_valid():
            category = serializer.save(vendor=vendor)  # Correctly assign the Vendor instance
            return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slug=None, format=None):
        # Update an existing category
        try:
            vendor = self.get_vendor(request.user)
            category = Category.objects.get(slug=slug, vendor=vendor)
        except (ValueError, Category.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        category_name = data.get('category_name')
        if category_name:
            data['slug'] = slugify(category_name)

        serializer = CategorySerializer(category, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug=None, format=None):
        # Delete an existing category
        try:
            vendor = self.get_vendor(request.user)
            category = Category.objects.get(slug=slug, vendor=vendor)
        except (ValueError, Category.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        category.delete()
        return Response({"message": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



