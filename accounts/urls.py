from django.urls import include, path

from . import api_views, views

urlpatterns = [
    path("registerUser/", views.registerUser, name="registerUser"),
    path("registerVendor/", views.registerVendor, name="registerVendor"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("myAccount/", views.myAccount, name="myAccount"),
    path("custDashboard/", views.custDashboard, name="custDashboard"),
    path("vendorDashboard/", views.vendorDashboard, name="vendorDashboard"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path(
        "reset_password_validate/<uidb64>/<token>/",
        views.reset_password_validate,
        name="reset_password_validate",
    ),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("vendor/", include("vendor.urls")),
    path('customer/', include('customers.urls')),
    # api_urlpattern
    path("api_register/", api_views.RegisterUserView.as_view(), name="register_user"),
    path(
        "api_register-vendor/",
        api_views.RegisterVendorView.as_view(),
        name="register_vendor",
    ),
    path("api_login/", api_views.LoginView.as_view(), name="api_login"),
    path("api_logout/", api_views.LogoutView.as_view(), name="api_logout"),
    path("api_user-details/", api_views.UserDetailView.as_view(), name="user-details"),
    path(
        "password-reset/", api_views.PasswordResetView.as_view(), name="password_reset"
    ),
]
