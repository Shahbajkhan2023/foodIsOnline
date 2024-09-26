from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from menu.models import Category, FoodItem
from vendor.models import Vendor

from .context_processors import get_cart_amounts, get_cart_counter
from .models import Cart
from django.shortcuts import render
from accounts.models import UserProfile
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from orders.forms import OrderForm


def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()
    context = {
        "vendors": vendors,
        "vendor_count": vendor_count,
    }
    return render(request, "marketplace/listings.html", context)


def vendor_detail(request, vendor_slug):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)

    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch("fooditems", queryset=FoodItem.objects.filter(is_available=True))
    )

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None
    context = {
        "vendor": vendor,
        "categories": categories,
        "cart_items": cart_items,
    }
    return render(request, "marketplace/vendor_detail.html", context)


def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    # Increase the cart quantity
                    chkCart.quantity += 1
                    chkCart.save()
                    return JsonResponse(
                        {
                            "status": "Success",
                            "message": "Increased the cart quantity",
                            "cart_counter": get_cart_counter(request),
                            "qty": chkCart.quantity,
                            "cart_amount": get_cart_amounts(request),
                        }
                    )
                except:
                    chkCart = Cart.objects.create(
                        user=request.user, fooditem=fooditem, quantity=1
                    )
                    return JsonResponse(
                        {
                            "status": "Success",
                            "message": "Added the food to the cart",
                            "cart_counter": get_cart_counter(request),
                            "qty": chkCart.quantity,
                            "cart_amount": get_cart_amounts(request),
                        }
                    )
            except:
                return JsonResponse(
                    {"status": "Failed", "message": "This food does not exist!"}
                )
        else:
            return JsonResponse({"status": "Failed", "message": "Invalid request!"})

    else:
        return JsonResponse(
            {"status": "login_required", "message": "Please login to continue"}
        )


def decrease_cart(request, food_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if chkCart.quantity > 1:
                        # decrease the cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0
                    return JsonResponse(
                        {
                            "status": "Success",
                            "cart_counter": get_cart_counter(request),
                            "qty": chkCart.quantity,
                            "cart_amount": get_cart_amounts(request),
                        }
                    )
                except:
                    return JsonResponse(
                        {
                            "status": "Failed",
                            "message": "You do not have this item in your cart!",
                        }
                    )
            except:
                return JsonResponse(
                    {"status": "Failed", "message": "This food does not exist!"}
                )
        else:
            return JsonResponse({"status": "Failed", "message": "Invalid request!"})

    else:
        return JsonResponse(
            {"status": "login_required", "message": "Please login to continue"}
        )


@login_required(login_url="login")
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by("created_at")
    context = {
        "cart_items": cart_items,
    }
    return render(request, "marketplace/cart.html", context)


def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            try:
                # Check if the cart item exists
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse(
                        {
                            "status": "Success",
                            "message": "Cart item has been deleted!",
                            "cart_counter": get_cart_counter(request),
                            "cart_amount": get_cart_amounts(request),
                        }
                    )
            except:
                return JsonResponse(
                    {"status": "Failed", "message": "Cart Item does not exist!"}
                )
        else:
            return JsonResponse({"status": "Failed", "message": "Invalid request!"})


def search(request):
    # Get search parameters from the request
    keyword = request.GET.get('keyword', '').strip()
    address = request.GET.get('address', '').strip()

    # Start with the basic Vendor queryset
    vendors = Vendor.objects.all()

    # Filter vendors by vendor_name if provided
    if keyword:
        vendors = vendors.filter(vendor_name__icontains=keyword)

    # Filter vendors by location if provided
    if address:
        # Ensure UserProfile with matching location is fetched
        matching_profiles = UserProfile.objects.filter(location__icontains=address)
        vendors = vendors.filter(user_profile__in=matching_profiles)

    # Get the count of vendors
    vendor_count = vendors.count()

    # Prepare context for the template
    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
        'source_location': address,
    }

    # Render the results in the template
    return render(request, 'marketplace/listings.html', context)


class CheckoutView(LoginRequiredMixin, TemplateView):
    login_url = 'login'  # Redirect to login page if not authenticated
    template_name = 'marketplace/checkout.html'  # Template to render

    def get_cart_items(self):
        """Retrieve cart items for the logged-in user."""
        return Cart.objects.filter(user=self.request.user).order_by('created_at')

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