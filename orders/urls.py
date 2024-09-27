from django.urls import path
from . import views


urlpatterns = [
    path('place-order/', views.PlaceOrderView.as_view(), name='place_order'),
]