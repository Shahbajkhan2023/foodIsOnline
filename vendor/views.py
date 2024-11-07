from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.http import JsonResponse
from django.db import IntegrityError

from accounts.forms import UserProfileForm
from accounts.models import UserProfile
from accounts.views import check_role_vendor
from menu.forms import CategoryForm, FoodItemForm
from menu.models import Category, FoodItem

from .forms import VendorForm, OpeningHourForm
from .models import Vendor, OpeningHour

from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, FormView, UpdateView,DeleteView
from .mixins import AjaxAuthenticationMixin
from .utils import get_vendor
from django.urls import reverse_lazy
from django.urls import reverse
from django.contrib.messages.views import SuccessMessageMixin



class VendorProfile(View):
    template_name = "vendor/vprofile.html"

    def get_object(self):
        profile = get_object_or_404(UserProfile, user=self.request.user)
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return profile, vendor

    def get_context_data(self, profile, vendor, profile_form, vendor_form):
        return {
            'profile_form': profile_form,
            'vendor_form': vendor_form,
            'profile': profile,
            'vendor': vendor,
        }

    def get(self, request, *args, **kwargs):
        profile, vendor = self.get_object()
        profile_form = UserProfileForm(instance=profile)
        vendor_form = VendorForm(instance=vendor)
        context = self.get_context_data(profile, vendor, profile_form, vendor_form)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        profile, vendor = self.get_object()
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        vendor_form = VendorForm(request.POST, request.FILES, instance=vendor)

        if profile_form.is_valid() and vendor_form.is_valid():
            profile_form.save()
            vendor_form.save()
            messages.success(request, "Settings updated.")
            return redirect("vprofile")
        else:
            messages.error(request, "There were errors in your form. Please correct them.")

        context = self.get_context_data(profile, vendor, profile_form, vendor_form)
        return render(request, self.template_name, context)


class MenuBuilder(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Category
    template_name = "vendor/menu_builder.html"
    context_object_name = "categories"
    login_url = "login"  

    def test_func(self):
        # Assuming `check_role_vendor` is the function that checks if user is a vendor
        return check_role_vendor(self.request.user)

    def get_queryset(self):
        vendor = get_vendor(self.request)
        return Category.objects.filter(vendor=vendor).order_by("created_at")


class FoodItemsByCategory(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = FoodItem
    template_name = "vendor/fooditems_by_category.html"
    context_object_name = "fooditems"
    login_url = "login"  

    def test_func(self):
        return check_role_vendor(self.request.user)

    def get_queryset(self):
        vendor = get_vendor(self.request)  # Get the logged-in vendor
        self.category = get_object_or_404(Category, pk=self.kwargs['pk'], vendor=vendor)
        return FoodItem.objects.filter(category=self.category)  # Filter food items by the selected category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
    

class AddCategory(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = "vendor/add_category.html"
    form_class = CategoryForm
    success_url = reverse_lazy("menu_builder")  

    def test_func(self):
        return check_role_vendor(self.request.user)

    def form_valid(self, form):
        category_name = form.cleaned_data["category_name"]
        category = form.save(commit=False) 
        category.vendor = get_vendor(self.request)  # Assign the vendor to the category
        category.slug = slugify(category_name)  # Generate slug from category name
        category.save()  
        messages.success(self.request, "Category added successfully!")  
        return super().form_valid(form) 


class EditCategory(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "vendor/edit_category.html"
    context_object_name = "category"
    success_url = reverse_lazy("menu_builder")
    success_message = "Category updated successfully!"

    def test_func(self):
        return check_role_vendor(self.request.user)

    def form_valid(self, form):
        category = form.save(commit=False)
        category_name = form.cleaned_data["category_name"]
        category.slug = slugify(category_name)
        category.vendor = get_vendor(self.request)
        category.save()
        return super().form_valid(form)


class DeleteCategory(LoginRequiredMixin, UserPassesTestMixin, View): 

    def test_func(self):
        return check_role_vendor(self.request.user)

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        messages.success(request, "Category has been deleted successfully!")
        return redirect("menu_builder")


class AddFood(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = FoodItem
    form_class = FoodItemForm
    template_name = "vendor/add_food.html"
    success_url = reverse_lazy("menu_builder")  # Redirect URL on success

    def form_valid(self, form):
        food = form.save(commit=False) 
        food.vendor = get_vendor(self.request)  # Associate with the current vendor
        food.slug = slugify(form.cleaned_data["food_title"]) 
        food.save()  
        messages.success(self.request, "Food Item added successfully!")
        return super().form_valid(form)  
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set queryset for the category field based on the logged-in vendor
        form.fields["category"].queryset = Category.objects.filter(vendor=get_vendor(self.request))
        return form

    def test_func(self):
        return check_role_vendor(self.request.user)  # Ensure the user has the vendor role


class EditFood(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = FoodItem
    form_class = FoodItemForm
    template_name = "vendor/edit_food.html"
    context_object_name = "food"
    success_url = reverse_lazy("menu_builder")  
    login_url = "login"
    success_message = "Food Item updated successfully!"

    def test_func(self):
        return check_role_vendor(self.request.user)

    def get_queryset(self):
        return FoodItem.objects.filter(category__vendor=get_vendor(self.request))

    def form_valid(self, form):
        food = form.save(commit=False)
        food.vendor = get_vendor(self.request)  
        food.slug = slugify(form.cleaned_data["food_title"])  
        food.save() 
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["category"].queryset = Category.objects.filter(vendor=get_vendor(self.request))
        return form


class DeleteFood(LoginRequiredMixin, UserPassesTestMixin, View):
   
    def test_func(self):
        return check_role_vendor(self.request.user)

    def get(self, request, pk):
        food = get_object_or_404(FoodItem, pk=pk, category__vendor=get_vendor(request))
        food.delete()
        messages.success(request, "Food Item has been deleted successfully!") 
        return redirect("fooditems_by_category", food.category.id) 
    

class OpeningHoursView(ListView):
    model = OpeningHour
    template_name = 'vendor/opening_hours.html'
    context_object_name = 'opening_hours'

    def get_queryset(self):
        return OpeningHour.objects.filter(vendor=get_vendor(self.request))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = OpeningHourForm()
        return context


class AddOpeningHoursView(AjaxAuthenticationMixin, CreateView):
    model = OpeningHour
    form_class = OpeningHourForm

    def form_valid(self, form):
        form.instance.vendor = get_vendor(self.request)

        try:
            opening_hour = form.save()
            return JsonResponse(self.success_response(opening_hour))
        except IntegrityError:
            return JsonResponse(self.error_response(form), status=400)

    def success_response(self, opening_hour):
        return {
            'status': 'success',
            'id': opening_hour.id,
            'day': opening_hour.get_day_display(),
            'is_closed': 'Closed' if opening_hour.is_closed else None,
            'from_hour': opening_hour.from_hour if not opening_hour.is_closed else None,
            'to_hour': opening_hour.to_hour if not opening_hour.is_closed else None,
        }

    def error_response(self, form):
        return {
            'status': 'failed',
            'message': f"{form.cleaned_data['from_hour']}-{form.cleaned_data['to_hour']} already exists for this day!"
        }
    
class RemoveOpeningHoursView(AjaxAuthenticationMixin, View):
    def get(self, request, pk):
        hour = get_object_or_404(OpeningHour, pk=pk)
        hour.delete()
        return JsonResponse({'status': 'success', 'id': pk})