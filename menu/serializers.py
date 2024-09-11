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



class FoodItemCreateSerializer(serializers.ModelSerializer):
    category_slug = serializers.CharField(write_only=True)  # Accept category slug as input
    image = serializers.ImageField(required=False, allow_null=True)  # Make image field optional

    class Meta:
        model = FoodItem
        fields = ['food_title', 'slug', 'description', 'price', 'image', 'is_available', 'category_slug']

    def create(self, validated_data):
        category_slug = validated_data.pop('category_slug')
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            raise serializers.ValidationError({'category_slug': 'Invalid category slug'})

        # Retrieve vendor from request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'vendor'):
            vendor = request.user.vendor
        else:
            raise serializers.ValidationError({'vendor': 'Vendor not found for the current user'})

        return FoodItem.objects.create(category=category, vendor=vendor, **validated_data)

    def update(self, instance, validated_data):
        category_slug = validated_data.pop('category_slug', None)
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                instance.category = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category_slug': 'Invalid category slug'})

        # Update other fields
        instance.food_title = validated_data.get('food_title', instance.food_title)
        instance.slug = validated_data.get('slug', instance.slug)
        instance.description = validated_data.get('description', instance.description)
        instance.price = validated_data.get('price', instance.price)
        instance.image = validated_data.get('image', instance.image)
        instance.is_available = validated_data.get('is_available', instance.is_available)

        instance.save()
        return instance
