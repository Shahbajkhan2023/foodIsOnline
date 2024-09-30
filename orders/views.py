from .utils import generate_order_number
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import  Order
from marketplace.models import Cart
from .forms import OrderForm
from marketplace.context_processors import get_cart_amounts



class PlaceOrderView(LoginRequiredMixin, FormView):
    login_url = 'login'
    template_name = 'orders/place_order.html'
    form_class = OrderForm

    def get_cart_data(self, cart_items):
        amounts = get_cart_amounts(self.request)
        return {
            'cart_items': cart_items,
            'subtotal': amounts['subtotal'],
            'total_tax': amounts['tax'],
            'grand_total': amounts['grand_total'],
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = Cart.objects.filter(user=self.request.user).order_by('created_at')
        
        # Redirect to marketplace if the cart is empty
        if not cart_items.exists():
            return redirect('marketplace')

        context.update(self.get_cart_data(cart_items))
        return context

    def form_valid(self, form):
        order = self.create_order(form)
        return self.render_to_response(self.get_context_data(order=order))

    def create_order(self, form):
        amounts = get_cart_amounts(self.request)
        order = Order.objects.create(
            user=self.request.user,
            total=amounts['grand_total'],
            total_tax=amounts['tax'],
            payment_method=self.request.POST['payment_method'],
            **form.cleaned_data
        )
        order.order_number = generate_order_number(order.id)
        order.save()  # Update order number
        return order
