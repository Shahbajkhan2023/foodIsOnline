from django.urls import path
from . import views


urlpatterns = [
    path('place-order/', views.PlaceOrderView.as_view(), name='place_order'),
    path('config/', views.StripeConfig.as_view(), name='stripe_config'),
    path('create-checkout-session/', views.CreateCheckoutSession.as_view(), name='create_checkout_session'),
    path('payments/', views.PaymentsView.as_view(), name='payments'),
]