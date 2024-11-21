from django.contrib import admin

from .models import Category, FoodItem


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("category_name",)}
    list_display = ("category_name", "vendor", "updated_at")
    search_fields = ("category_name", "vendor__vendor_name")


class FoodItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("food_title",)}
    list_display = (
        "food_title",
        "category",
        "get_vendor",
        "price",
        "is_available",
        "updated_at",
    )
    search_fields = (
        "food_title",
        "category__category_name",
        "category__vendor__vendor_name",
        "price",
    )
    list_filter = ("is_available",)

    # Method to display the vendor in the FoodItem list
    def get_vendor(self, obj):
        return obj.category.vendor.vendor_name

    get_vendor.short_description = 'Vendor'  # Column name in admin



admin.site.register(Category, CategoryAdmin)
admin.site.register(FoodItem, FoodItemAdmin)
