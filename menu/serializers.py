from rest_framework import serializers

from .models import Category, FoodItem


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = ["food_title", "slug", "description", "price", "image", "is_available"]


class CategorySerializer(serializers.ModelSerializer):
    fooditems = FoodItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["category_name", "slug", "description", "fooditems"]


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = ['id', 'vendor', 'category', 'food_title', 'slug', 'description', 'price', 'image', 'is_available']
        read_only_fields = ['vendor', 'slug']

    # Make category and image optional
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    image = serializers.ImageField(required=False, allow_null=True)
