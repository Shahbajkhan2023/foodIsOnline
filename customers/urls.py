from django.urls import path
from accounts import views as AccountViews
from . import views


urlpatterns = [
    path('', AccountViews.custDashboard, name='customer'),
    path('profile/', views.CProfileView.as_view(), name='cprofile'),
    path('my-orders/', views.MyOrdersView.as_view(), name='my_orders'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]





