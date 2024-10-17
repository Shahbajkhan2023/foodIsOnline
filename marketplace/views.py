from django.views.generic import ListView
from django.views.generic import DetailView
from django.views import View
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from menu.models import Category, FoodItem
from vendor.models import Vendor

from .context_processors import get_cart_amounts, get_cart_counter
from marketplace.models import Cart as cart_model
from django.shortcuts import render
from accounts.models import UserProfile
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from orders.forms import OrderForm


class Marketplace(ListView):
    model = Vendor
    template_name = "marketplace/listings.html"
    context_object_name = "vendors"
    
    def get_queryset(self):
        return Vendor.objects.filter(is_approved=True, user__is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vendor_count"] = self.get_queryset().count() 
        return context


class VendorDetail(DetailView):
    model = Vendor
    template_name = "marketplace/vendor_detail.html"
    context_object_name = "vendor"

    def get_object(self):
        return get_object_or_404(Vendor, vendor_slug=self.kwargs['vendor_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the current vendor object
        vendor = self.object
        # Fetch categories and their available food items
        context["categories"] = self.get_categories_with_fooditems(vendor)
        # Check if the user is authenticated and get cart items if they are
        context["cart_items"] = self.get_cart_items()
        return context

    def get_categories_with_fooditems(self, vendor):
        return Category.objects.filter(vendor=vendor).prefetch_related(
            Prefetch("fooditems", queryset=FoodItem.objects.filter(is_available=True))
        )

    def get_cart_items(self):
        if self.request.user.is_authenticated:
            return cart_model.objects.filter(user=self.request.user)
        return None
    

class AddToCart(View):
    def get(self, request, food_id):
        if not request.user.is_authenticated:
            return self.login_required_response()

        if not self.is_ajax_request(request):
            return self.invalid_request_response()

        fooditem = self.get_food_item(food_id)
        if fooditem is None:
            return self.food_not_exist_response()

        # Create a cart item with a default quantity of 1 if it doesn't exist
        chkCart, created = cart_model.objects.get_or_create(user=request.user, fooditem=fooditem, defaults={'quantity': 1})

        if not created:
            return self.increase_cart_quantity(chkCart)
        else:
            return self.add_new_food_to_cart(chkCart)

    def is_ajax_request(self, request):
        return request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def get_food_item(self, food_id):
        """Retrieve the food item by ID."""
        try:
            return FoodItem.objects.get(id=food_id)
        except FoodItem.DoesNotExist:
            return None

    def increase_cart_quantity(self, chkCart):
        chkCart.quantity += 1
        chkCart.save()
        return JsonResponse(
            {
                "status": "Success",
                "message": "Increased the cart quantity",
                "cart_counter": get_cart_counter(self.request),
                "qty": chkCart.quantity,
                "cart_amount": get_cart_amounts(self.request),
            }
        )

    def add_new_food_to_cart(self, chkCart):
        chkCart.quantity = 1  # This should not be necessary because we set it in get_or_create
        chkCart.save()
        return JsonResponse(
            {
                "status": "Success",
                "message": "Added the food to the cart",
                "cart_counter": get_cart_counter(self.request),
                "qty": chkCart.quantity,
                "cart_amount": get_cart_amounts(self.request),
            }
        )

    def login_required_response(self):
        return JsonResponse(
            {"status": "login_required", "message": "Please login to continue"}
        )

    def invalid_request_response(self):
        return JsonResponse({"status": "Failed", "message": "Invalid request!"})

    def food_not_exist_response(self):
        return JsonResponse(
            {"status": "Failed", "message": "This food does not exist!"}
        )


class DecreaseCart(View):
    def get(self, request, food_id):
        """Handle the decrease of food items from the cart."""
        if not request.user.is_authenticated:
            return self.login_required_response()

        if not self.is_ajax_request(request):
            return self.invalid_request_response()

        fooditem = self.get_food_item(food_id)
        if fooditem is None:
            return self.food_not_exist_response()

        return self.decrease_cart_quantity(request.user, fooditem)

    def is_ajax_request(self, request):
        return request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def get_food_item(self, food_id):
        """Retrieve the food item by ID."""
        try:
            return FoodItem.objects.get(id=food_id)
        except FoodItem.DoesNotExist:
            return None

    def decrease_cart_quantity(self, user, fooditem):
        try:
            chkCart = cart_model.objects.get(user=user, fooditem=fooditem)
            if chkCart.quantity > 1:
                # Decrease the cart quantity
                chkCart.quantity -= 1
                chkCart.save()
                return self.success_response("Decreased the cart quantity", chkCart)
            else:
                # Remove item from cart if quantity is 1
                chkCart.delete()
                return self.success_response("Removed the item from cart", None)
        except cart_model.DoesNotExist:
            return self.cart_item_not_exist_response()

    def success_response(self, message, chkCart):
        qty = chkCart.quantity if chkCart else 0
        return JsonResponse(
            {
                "status": "Success",
                "message": message,
                "cart_counter": get_cart_counter(self.request),
                "qty": qty,
                "cart_amount": get_cart_amounts(self.request),
            }
        )

    def cart_item_not_exist_response(self):
        return JsonResponse(
            {
                "status": "Failed",
                "message": "You do not have this item in your cart!",
            }
        )

    def login_required_response(self):
        return JsonResponse(
            {"status": "login_required", "message": "Please login to continue"}
        )

    def invalid_request_response(self):
        return JsonResponse({"status": "Failed", "message": "Invalid request!"})

    def food_not_exist_response(self):
        return JsonResponse(
            {"status": "Failed", "message": "This food does not exist!"}
        )


class Cart(LoginRequiredMixin, ListView):
    model = cart_model
    template_name = "marketplace/cart.html"
    context_object_name = "cart_items"
    ordering = ["created_at"] 

    def get_queryset(self):
        return cart_model.objects.filter(user=self.request.user).order_by("created_at")



class DeleteCart(View):
    def get(self, request, cart_id):
        """Handle the deletion of a cart item."""
        if not request.user.is_authenticated:
            return self.login_required_response()

        if not self.is_ajax_request(request):
            return self.invalid_request_response()

        cart_item = self.get_cart_item(request.user, cart_id)
        if cart_item is None:
            return self.cart_item_not_exist_response()

        cart_item.delete()
        return self.success_response("Cart item has been deleted!")

    def is_ajax_request(self, request):
        return request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def get_cart_item(self, user, cart_id):
        try:
            return cart_model.objects.get(user=user, id=cart_id)
        except cart_model.DoesNotExist:
            return None

    def success_response(self, message):
        return JsonResponse(
            {
                "status": "Success",
                "message": message,
                "cart_counter": get_cart_counter(self.request),
                "cart_amount": get_cart_amounts(self.request),
            }
        )

    def login_required_response(self):
        return JsonResponse(
            {"status": "login_required", "message": "Please login to continue"}
        )

    def invalid_request_response(self):
        return JsonResponse({"status": "Failed", "message": "Invalid request!"})

    def cart_item_not_exist_response(self):
        return JsonResponse(
            {"status": "Failed", "message": "Cart Item does not exist!"}
        )


class Search(ListView):
    model = Vendor
    template_name = 'marketplace/listings.html'  
    context_object_name = 'vendors'  

    def get_queryset(self):
        keyword = self.request.GET.get('keyword', '').strip()
        address = self.request.GET.get('address', '').strip()
        vendors = Vendor.objects.all()

        if keyword:
            vendors = vendors.filter(vendor_name__icontains=keyword)

        if address:
            matching_profiles = UserProfile.objects.filter(location__icontains=address)
            vendors = vendors.filter(user_profile__in=matching_profiles)

        return vendors

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor_count'] = self.get_queryset().count()  
        context['source_location'] = self.request.GET.get('address', '').strip()  
        return context


class CheckoutView(LoginRequiredMixin, TemplateView):
    login_url = 'login'  
    template_name = 'marketplace/checkout.html'  

    def get_cart_items(self):
        """Retrieve cart items for the logged-in user."""
        return cart_model.objects.filter(user=self.request.user).order_by('created_at')

    def get_user_profile(self):
        """Get user profile details for the logged-in user."""
        return UserProfile.objects.get(user=self.request.user)

    def get_default_values(self):
        """Prepare default values for the order form."""
        user_profile = self.get_user_profile()
        return {
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
            'phone': self.request.user.phone_number,
            'email': self.request.user.email,
            'address': user_profile.address,
            'country': user_profile.country,
            'state': user_profile.state,
            'city': user_profile.city,
            'pin_code': user_profile.pin_code,
        }

    def get_context_data(self, **kwargs):
        """Add context data to the template."""
        context = super().get_context_data(**kwargs)
        cart_items = self.get_cart_items()
        cart_count = cart_items.count()

        if cart_count <= 0:
            return redirect('marketplace')  # Redirect if cart is empty

        context['form'] = OrderForm(initial=self.get_default_values())
        context['cart_items'] = cart_items
        return context
    


    