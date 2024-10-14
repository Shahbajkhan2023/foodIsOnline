from django.views.generic.edit import CreateView
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.core.mail import message
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify
from django.utils.http import urlsafe_base64_decode

from vendor.forms import VendorForm
from vendor.models import Vendor

from .forms import UserForm
from .models import User, UserProfile
from .utils import detectUser, send_verification_email

from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import PasswordChangeForm
from orders.models import Order

# Restrict the vendor from accessing the customer page
def check_role_vendor(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied


# Restrict the customer from accessing the vendor page
def check_role_customer(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied



class RegisterUserView(CreateView):
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

 

class RegisterVendorView(CreateView):
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



def activate(request, uidb64, token):
    # Activate the user by setting the is_active status to True
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulation! Your account is activated.")
        return redirect("myAccount")
    else:
        messages.error(request, "Invalid activation link")
        return redirect("myAccount")


def login(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect("myAccount")
    elif request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        print(email, password)
        user = auth.authenticate(email=email, password=password)

        if user is not None:
            print("user is none")
            auth.login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("home")
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("login")
    return render(request, "accounts/login.html")


def logout(request):
    auth.logout(request)
    messages.info(request, "You are logged out.")
    return redirect("login")


@login_required(login_url="login")
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)


@login_required(login_url="login")
@user_passes_test(check_role_customer)
def custDashboard(request):
    recent_orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'recent_orders' : recent_orders,
    }
    return render(request, "accounts/custDashboard.html", context)


@login_required(login_url="login")
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, "accounts/vendorDashboard.html")


def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            # send reset password email
            mail_subject = "Reset Your Password"
            email_template = "accounts/emails/reset_password_email.html"
            send_verification_email(request, user, mail_subject, email_template)

            messages.success(
                request, "Password reset link has been sent to your email address."
            )
            return redirect("login")
        else:
            messages.error(request, "Account does not exist")
            return redirect("forgot_password")
    return render(request, "accounts/forgot_password.html")


def reset_password_validate(request, uidb64, token):
    # validate the user by decoding the token and user pk
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.info(request, "Please reset your password")
        return redirect("reset_password")
    else:
        messages.error(request, "This link has been expired!")
        return redirect("myAccount")


def reset_password(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password == confirm_password:
            pk = request.session.get("uid")
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("login")
        else:
            messages.error(request, "Password do not match!")
            return redirect("reset_password")
    return render(request, "accounts/reset_password.html")



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
