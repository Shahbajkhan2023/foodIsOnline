from django.urls import path
from accounts import views as AccountViews
from . import views


urlpatterns = [
    path('', AccountViews.custDashboard, name='customer'),
    path('profile/', views.CProfileView.as_view(), name='cprofile'),
]





