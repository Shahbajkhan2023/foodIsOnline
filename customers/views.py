from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from accounts.forms import UserInfoForm, UserProfileForm
from accounts.models import UserProfile
from orders.models import Order, OrderedFood
from django.views.generic import ListView, DetailView


class CProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'customers/cprofile.html'
    success_url = reverse_lazy('cprofile')

    def get_object(self):
        # Get the UserProfile for the logged-in user
        return get_object_or_404(UserProfile, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserInfoForm(instance=self.request.user)
        return context

    def form_valid(self, form):
        user_form = UserInfoForm(self.request.POST, instance=self.request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(self.request, 'Profile updated successfully!')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['user_form'] = UserInfoForm(instance=self.request.user)
        return self.render_to_response(context)


class MyOrdersView(ListView):
    model = Order
    template_name = 'customers/my_orders.html'  
    context_object_name = 'orders'  # The context variable to use in the template

    def get_queryset(self):
        # Filter the orders for the current user and only those that are ordered
        return Order.objects.filter(user=self.request.user, is_ordered=True).order_by('-created_at')
    

class OrderDetailView(DetailView):
    model = Order
    template_name = 'customers/order_detail.html'  
    context_object_name = 'order'  

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class VendorOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'vendor/vendor_orders.html'
    context_object_name = 'orders'
    login_url = 'login'

    def get_queryset(self):
        # Fetch the current vendor
        current_vendor = self.request.user.user  # Assuming the user has a OneToOne relationship with Vendor
        return Order.objects.filter(vendor=current_vendor).order_by('-created_at')

    def get_context_data(self, **kwargs):
        # Add vendor information to the context
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.user  # Assuming user has OneToOne relation with Vendor
        return context
    

class VendorOrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name =  'vendor/vendor_order_detail.html'
    context_object_name = 'order'
    login_url = 'login'

    def get_queryset(self):
        current_vendor = self.request.user.user
        return Order.objects.filter(vendor=current_vendor)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ordered_food_items'] = OrderedFood.objects.filter(order=self.object)
        return context