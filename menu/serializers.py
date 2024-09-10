from rest_framework import serializers
from .models import Category, FoodItem


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = ['food_title', 'slug', 'description', 'price', 'image', 'is_available']


class CategorySerializer(serializers.ModelSerializer):
    fooditems = FoodItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['category_name', 'slug', 'description', 'fooditems']
