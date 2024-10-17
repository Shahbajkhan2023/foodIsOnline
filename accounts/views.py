from django.views.generic.edit import CreateView
from django.contrib import auth, messages
from django.views import View
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.core.mail import message
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify
from django.utils.http import urlsafe_base64_decode

from vendor.forms import VendorForm

from .forms import UserForm
from .models import User, UserProfile
from .utils import detectUser, send_verification_email, check_role_customer, check_role_vendor

from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import PasswordChangeForm
from orders.models import Order


class RegisterUser(CreateView):
    template_name = "accounts/registerUser.html"
    form_class = UserForm
    success_url = reverse_lazy("registerUser")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("custDashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.create_user(form)
        self.send_verification_email(user)
        messages.success(self.request, "Your account has been registered successfully!")
        return super().form_valid(form)

    def create_user(self, form):
        user = User.objects.create_user(**form.cleaned_data)
        user.role = User.CUSTOMER
        user.save()
        return user

    def send_verification_email(self, user):
        mail_subject = "Please activate your account"
        email_template = "accounts/emails/account_verification_email.html"
        send_verification_email(self.request, user, mail_subject, email_template)

 
class RegisterVendor(CreateView):
    template_name = "accounts/registerVendor.html"
    form_class = UserForm
    success_url = reverse_lazy("registerVendor")  

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in!")
            return redirect("myAccount")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """To include both UserForm and VendorForm in the context."""
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["v_form"] = VendorForm(self.request.POST, self.request.FILES)
        else:
            context["v_form"] = VendorForm()
        return context

    def form_valid(self, form):
        v_form = VendorForm(self.request.POST, self.request.FILES)

        if form.is_valid() and v_form.is_valid():
            # Create the user
            user = self.create_user(form)
            # Create the vendor
            self.create_vendor(v_form, user)

            # Send verification email
            self.send_verification_email(user)

            messages.success(
                self.request,
                "Your account has been registered successfully! Please wait for approval.",
            )
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def create_user(self, form):
        user = User.objects.create_user(**form.cleaned_data)
        user.role = User.VENDOR
        user.save()
        return user

    def create_vendor(self, v_form, user):
        vendor = v_form.save(commit=False)
        vendor.user = user
        vendor_name = v_form.cleaned_data["vendor_name"]
        vendor.vendor_slug = slugify(vendor_name) + "-" + str(user.id)
        user_profile = UserProfile.objects.get(user=user)
        vendor.user_profile = user_profile
        vendor.save()

    def send_verification_email(self, user):
        mail_subject = "Please activate your account"
        email_template = "accounts/emails/account_verification_email.html"
        send_verification_email(self.request, user, mail_subject, email_template)

    def form_invalid(self, form):
        v_form = VendorForm(self.request.POST, self.request.FILES)
        return self.render_to_response(self.get_context_data(form=form, v_form=v_form))


class Activate(View):
    
    def get(self, request, uidb64, token):
        user = self.get_user_from_uid(uidb64)

        if user and self.is_token_valid(user, token):
            self.activate_user(user)
            messages.success(request, "Congratulations! Your account is activated.")
            return redirect("myAccount")
        else:
            messages.error(request, "Invalid activation link.")
            return redirect("myAccount")

    def get_user_from_uid(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def is_token_valid(self, user, token):
        return default_token_generator.check_token(user, token)

    def activate_user(self, user):
        user.is_active = True
        user.save()


class Login(View):
    template_name = "accounts/login.html"

    def get(self, request):
        # If the user is already authenticated, redirect them
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
    login_url = 'login'  # Redirect to login if not authenticated

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
        
        if self.is_email_valid(email):
            user = self.get_user_by_email(email)
            self.send_reset_email(request, user)
            messages.success(request, "Password reset link has been sent to your email address.")
            return redirect("login")
        else:
            messages.error(request, "Account does not exist.")
            return redirect("forgot_password")

    def is_email_valid(self, email):
        return User.objects.filter(email=email).exists()

    def get_user_by_email(self, email):
        return User.objects.get(email=email)

    def send_reset_email(self, request, user):
        mail_subject = "Reset Your Password"
        email_template = "accounts/emails/reset_password_email.html"
        send_verification_email(request, user, mail_subject, email_template)


class ResetPasswordValidate(View):
    def get(self, request, uidb64, token):
        """Validate the user by decoding the token and user pk."""
        user = self.get_user(uidb64)

        if self.is_valid_user(user, token):
            self.set_user_session(request, user.id)
            messages.info(request, "Please reset your password.")
            return redirect("reset_password")
        else:
            messages.error(request, "This link has expired!")
            return redirect("myAccount")

    def get_user(self, uidb64):
        """Decode the uid and retrieve the user."""
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def is_valid_user(self, user, token):
        return user is not None and default_token_generator.check_token(user, token)

    def set_user_session(self, request, uid):
        request.session["uid"] = uid


class ResetPassword(View):
    template_name = "accounts/reset_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        password, confirm_password = self.get_passwords(request)

        if self.passwords_match(password, confirm_password):
            # Get the user and reset the password
            user = self.get_user(request)
            self.reset_user_password(user, password)

            messages.success(request, "Password reset successful")
            return redirect("login")
        else:
            messages.error(request, "Passwords do not match!")
            return redirect("reset_password")

    def get_passwords(self, request):
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        return password, confirm_password

    def passwords_match(self, password, confirm_password):
        return password == confirm_password

    def get_user(self, request):
        pk = request.session.get("uid")
        return User.objects.get(pk=pk)

    def reset_user_password(self, user, password):
        user.set_password(password)
        user.is_active = True
        user.save()


class PasswordChangeView(FormView):
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('logout')

    def get_form_kwargs(self):
        """Pass the current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass the logged-in user
        return kwargs

    def form_valid(self, form):
        """If form is valid, change password."""
        user = self.request.user
        new_password = form.cleaned_data['new_password']
        user.set_password(new_password)
        user.save()

        # Keep the user logged in after the password change
        update_session_auth_hash(self.request, user)

        messages.success(self.request, "Password changed successfully.")
        return super().form_valid(form)
