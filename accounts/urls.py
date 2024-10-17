from django.urls import include, path
from . import api_views, views

urlpatterns = [
    path("registerUser/", views.RegisterUser.as_view(), name="registerUser"),
    path("registerVendor/", views.RegisterVendor.as_view(), name="registerVendor"),    
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(next_page='login'), name='logout'),
    path("myAccount/", views.MyAccount.as_view(), name="myAccount"),
    path("custDashboard/", views.CustDashboard.as_view(), name="custDashboard"),
    path("vendorDashboard/", views.VendorDashboard.as_view(), name="vendorDashboard"),
    path("activate/<uidb64>/<token>/", views.Activate.as_view(), name="activate"),
    path("forgot_password/", views.ForgotPassword.as_view(), name="forgot_password"),
    path(
        "reset_password_validate/<uidb64>/<token>/",
        views.ResetPasswordValidate.as_view(),
        name="reset_password_validate",
    ),
    path("reset_password/", views.ResetPassword.as_view(), name="reset_password"),
    path('change-password/', views.PasswordChangeView.as_view(), name='password_change'),
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
