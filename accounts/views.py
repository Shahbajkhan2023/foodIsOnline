from django.contrib import auth, messages
from django.views import View
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify
from django.utils.http import urlsafe_base64_decode

from vendor.forms import VendorForm
from .forms import UserForm
from .models import User, UserProfile
from .utils import detectUser, check_role_customer, check_role_vendor

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import PasswordChangeForm
from orders.models import Order
from accounts.tasks import send_verification_email_task


class RegisterUser(View):
    template_name = "accounts/registerUser.html"

    def get(self, request):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("custDashboard")
        return render(request, self.template_name, {"form": UserForm()})

    
    def post(self, request):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("custDashboard")
        
        form = UserForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])  
            user.role = User.CUSTOMER
            user.save()

            mail_subject = "Please activate your account"
            email_template = "accounts/emails/account_verification_email.html"
            ngrok_url = f"https://{request.META['HTTP_HOST']}"

            # Enqueue Celery task with necessary data
            send_verification_email_task.delay(user.id, mail_subject, email_template, ngrok_url)
            messages.success(request, "Your account has been registered successfully!")
            return redirect("registerUser")
        return render(request, self.template_name, {"form": form})


class RegisterVendor(View):
    template_name = "accounts/registerVendor.html"

    def get(self, request):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("myAccount")
        return render(request, self.template_name, {"form": UserForm(), "v_form": VendorForm()})

    def post(self, request):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("myAccount")
        form, v_form = UserForm(request.POST), VendorForm(request.POST, request.FILES)
        if form.is_valid() and v_form.is_valid():
            user = User.objects.create_user(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )

            vendor = v_form.save(commit=False)
            vendor.user, vendor.vendor_slug = user, slugify(v_form.cleaned_data["vendor_name"]) + f"-{user.id}"
            vendor.user_profile = UserProfile.objects.get(user=user)
            vendor.save()
            ngrok_url = f"https://{request.META['HTTP_HOST']}"

            # Enqueue Celery task with necessary data
            send_verification_email_task.delay(user.id, "Please activate your account", "accounts/emails/account_verification_email.html", ngrok_url)
            messages.success(request, "Your account has been registered successfully! Please wait for the approval.")
            return redirect("registerVendor")
        return render(request, self.template_name, {"form": form, "v_form": v_form})


class Activate(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Congratulations! Your account is activated.")
            return redirect("myAccount")
        else:
            messages.error(request, "Invalid activation link")
            return redirect("myAccount")


class Login(View):
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("myAccount")
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("home")
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("login")


class Logout(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # Add the info message before logging out
        messages.info(request, "You are logged out.")
        return super().dispatch(request, *args, **kwargs)


class MyAccount(LoginRequiredMixin, View):
    login_url = 'login' 

    def get(self, request):
        user = request.user
        redirect_url = detectUser(user)  
        return redirect(redirect_url)


class CustDashboard(LoginRequiredMixin, TemplateView):
    template_name = "accounts/custDashboard.html" 
    login_url = 'login' 

    def dispatch(self, request, *args, **kwargs):
        # Perform role check
        if not check_role_customer(request.user):
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_orders'] = Order.objects.filter(user=self.request.user, is_ordered=True).order_by('-created_at')
        return context


class VendorDashboard(LoginRequiredMixin, TemplateView):
    template_name = "accounts/vendorDashboard.html" 
    login_url = 'login' 

    def dispatch(self, request, *args, **kwargs):
        # Perform role check
        if not check_role_vendor(request.user):
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)


class ForgotPassword(View):
    template_name = "accounts/forgot_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            mail_subject = "Reset Your Password"
            email_template = "accounts/emails/reset_password_email.html"
            ngrok_url = f"https://{request.META['HTTP_HOST']}"

            # Enqueue Celery task with necessary data
            send_verification_email_task.delay(user.id, mail_subject, email_template, ngrok_url)

            messages.success(request, "Password reset link has been sent to your email address.")
            return redirect("login")
        messages.error(request, "Account does not exist")
        return redirect("forgot_password")


class ResetPasswordValidate(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            request.session["uid"] = uid
            messages.info(request, "Please reset your password")
            return redirect("reset_password")
        else:
            messages.error(request, "This link has been expired!")
            return redirect("myAccount")
        

class ResetPassword(View):
    def get(self, request):
        return render(request, "accounts/reset_password.html")

    def post(self, request):
        password, confirm_password = request.POST.get("password"), request.POST.get("confirm_password")
        
        if password == confirm_password and request.session.get("uid"):
            user = User.objects.get(pk=request.session["uid"])
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("login")
        
        messages.error(request, "Passwords do not match or session expired")
        return redirect("reset_password")


class PasswordChangeView(View):
    template_name = 'accounts/password_change.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordChangeForm(user=request.user)})

    def post(self, request):
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")
            return redirect('logout')
        
        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})
