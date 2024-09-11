from django.urls import path
from . import views
from accounts import views as AccountViews
from . import api_views


urlpatterns = [
    path('', AccountViews.vendorDashboard, name='vendor'),
    path('profile/', views.vprofile, name='vprofile'),
    path('menu-builder/', views.menu_builder, name='menu_builder'),
    path('menu-builder/category/<int:pk>/', views.fooditems_by_category, name='fooditems_by_category'),

    # Category CRUD
    path('menu-builder/category/add/', views.add_category, name='add_category'),
    path('menu-builder/category/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('menu-builder/category/delete/<int:pk>/', views.delete_category, name='delete_category'),
    
    # FoodItem CRUD
    path('menu-builder/food/add/', views.add_food, name='add_food'),
    path('menu-builder/food/edit/<int:pk>/', views.edit_food, name='edit_food'),
    path('menu-builder/food/delete/<int:pk>/', views.delete_food, name='delete_food'),

    # api_views
    # category_api_view
    path('users/update/', api_views.UpdateUserView.as_view(), name='update_user'),
    path('fooditemsbycategory/', api_views.VendorFoodItemsByCategoryView.as_view(), name='vendor-fooditems-by-category'),
    path('fooditemsbycategory/<slug:slug>/', api_views.VendorFoodItemsByCategoryView.as_view(), name='category-detail-update-delete'),

    path('food/add/', api_views.FoodItemView.as_view(), name='food_item_create'),
    path('food/update/<slug:slug>/',  api_views.FoodItemView.as_view(), name='food_item_update'),
    path('food/delete/<slug:slug>/',  api_views.FoodItemView.as_view(), name='food_item_delete'),
]