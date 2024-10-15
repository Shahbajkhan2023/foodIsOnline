from django.urls import path

from accounts import views as AccountViews

from . import api_views, views


fooditem_list = api_views.FoodItemViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

fooditem_detail = api_views.FoodItemViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'delete': 'destroy'
})

urlpatterns = [
    path("", AccountViews.VendorDashboard.as_view(), name="vendor"),
    path("profile/", views.vprofile, name="vprofile"),
    path("menu-builder/", views.menu_builder, name="menu_builder"),
    path(
        "menu-builder/category/<int:pk>/",
        views.fooditems_by_category,
        name="fooditems_by_category",
    ),
    # Category CRUD
    path("menu-builder/category/add/", views.add_category, name="add_category"),
    path(
        "menu-builder/category/edit/<int:pk>/",
        views.edit_category,
        name="edit_category",
    ),
    path(
        "menu-builder/category/delete/<int:pk>/",
        views.delete_category,
        name="delete_category",
    ),
    # FoodItem CRUD
    path("menu-builder/food/add/", views.add_food, name="add_food"),
    path("menu-builder/food/edit/<int:pk>/", views.edit_food, name="edit_food"),
    path("menu-builder/food/delete/<int:pk>/", views.delete_food, name="delete_food"),
    # Opening Hour CRUD
    path('opening-hours/', views.OpeningHoursView.as_view(), name='opening_hours'),
    path('opening-hours/add/', views.AddOpeningHoursView.as_view(), name='add_opening_hours'),
    path('opening-hours/remove/<int:pk>/', views.RemoveOpeningHoursView.as_view(), name='remove_opening_hours'),
    
    # api_views
    path("users/update/", api_views.UpdateUserView.as_view(), name="update_user"),
    path(
        "fooditems/",
        api_views.VendorFoodItemsByCategoryView.as_view(),
        name="vendor-fooditems-by-category",
    ),
    path(
        "fooditems/<slug:slug>/",
        api_views.VendorFoodItemsByCategoryView.as_view(),
        name="category-detail-update-delete",
    ),
    path('api_fooditems/', fooditem_list, name='fooditem-list'),  # List and Create
    path('api_fooditems/<slug:slug>/', fooditem_detail, name='fooditem-detail'),  # Retrieve, Update, Delete

]
