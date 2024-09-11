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
    

    # api_views
    path('users/update/', api_views.UpdateUserView.as_view(), name='update_user'),
    path('fooditems/', api_views.VendorFoodItemsByCategoryView.as_view(), name='vendor-fooditems-by-category'),
    path('fooditems/<slug:slug>/', api_views.VendorFoodItemsByCategoryView.as_view(), name='category-detail-update-delete'),
]