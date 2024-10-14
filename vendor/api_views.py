from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from menu.models import Category, FoodItem
from menu.serializers import CategorySerializer, FoodItemSerializer

from .drf_custome_permission.permissions import IsVendor
from .models import Vendor
from .serializers import UserUpdateSerializer


class UpdateUserView(APIView):
    permission_classes = [
        IsAuthenticated
    ]  # Only authenticated users can access this view

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
            category_data.append(
                {
                    "category": CategorySerializer(category).data,
                    "fooditems": fooditem_data,
                }
            )

        return Response(category_data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        # Add a new category
        try:
            vendor = self.get_vendor(request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        category_name = data.get("category_name")
        data["slug"] = slugify(category_name)

        serializer = CategorySerializer(data=data)
        if serializer.is_valid():
            category = serializer.save(
                vendor=vendor
            )  # Correctly assign the Vendor instance
            return Response(
                CategorySerializer(category).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slug=None, format=None):
        # Update an existing category
        try:
            vendor = self.get_vendor(request.user)
            category = Category.objects.get(slug=slug, vendor=vendor)
        except (ValueError, Category.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        category_name = data.get("category_name")
        if category_name:
            data["slug"] = slugify(category_name)

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
        return Response(
            {"message": "Category deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class FoodItemViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsVendor]  # Ensure user is authenticated and is a vendor

    def list(self, request):
        
        # Fetch the vendor based on the authenticated user
        vendor = Vendor.objects.get(user=request.user)

        food_items = FoodItem.objects.filter(vendor=vendor)
        serializer = FoodItemSerializer(food_items, many=True)
        return Response(serializer.data)

    def create(self, request):
        category_slug = request.data.get('category_slug')
        category = get_object_or_404(Category, slug=category_slug)

        # Fetch the vendor based on the authenticated user
        vendor = Vendor.objects.get(user=request.user)

        serializer = FoodItemSerializer(data=request.data)
        if serializer.is_valid():
            # Save the food item with the vendor and category
            food_item = serializer.save(vendor=vendor, category=category)
            return Response(FoodItemSerializer(food_item).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, slug=None):

        # Fetch the vendor based on the authenticated user
        vendor = Vendor.objects.get(user=request.user)

        food_item = get_object_or_404(FoodItem, slug=slug, vendor=vendor)
        serializer = FoodItemSerializer(food_item)
        return Response(serializer.data)

    def update(self, request, slug=None):

        # Fetch the vendor based on the authenticated user
        vendor = Vendor.objects.get(user=request.user)

        food_item = get_object_or_404(FoodItem, slug=slug, vendor=vendor)
        category_slug = request.data.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            request.data['category'] = category.id

        serializer = FoodItemSerializer(food_item, data=request.data)
        if serializer.is_valid():
            food_item = serializer.save(vendor=vendor)
            return Response(FoodItemSerializer(food_item).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, slug=None):

        # Fetch the vendor based on the authenticated user
        vendor = Vendor.objects.get(user=request.user)

        food_item = get_object_or_404(FoodItem, slug=slug, vendor=request.user.vendor)
        food_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
