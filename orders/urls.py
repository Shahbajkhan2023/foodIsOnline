from django.urls import path
from . import views
from orders.views import StripeConfig
from .views import CreateCheckoutSession

urlpatterns = [
    path('place-order/', views.PlaceOrderView.as_view(), name='place_order'),
    path('config/', StripeConfig.as_view(), name='stripe_config'),
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create_checkout_session'),
    path('successed/', views.SuccessView.as_view()), # new
    path('cancelled/', views.CancelledView.as_view()), # new
    path('webhook/stripe/', views.StripeWeebhook.as_view())
]
