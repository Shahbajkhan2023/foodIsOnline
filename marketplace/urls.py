from django.urls import path

from . import views

urlpatterns = [
    path("", views.Marketplace.as_view(), name="marketplace"),
    path("<slug:vendor_slug>/", views.VendorDetail.as_view(), name="vendor_detail"),
    # ADD TO CART
    path("add_to_cart/<int:food_id>/", views.AddToCart.as_view(), name="add_to_cart"),
    # DECREASE CART
    path("decrease_cart/<int:food_id>/", views.DecreaseCart.as_view(), name="decrease_cart"),
    # DELETE CART ITEM
    path("delete_cart/<int:cart_id>/", views.DeleteCart.as_view(), name="delete_cart"),
]
