from .utils import generate_order_number
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import  Order
from marketplace.models import Cart
from .forms import OrderForm
from marketplace.context_processors import get_cart_amounts
from accounts.utils import send_notification
from django.http import JsonResponse
from .models import Payment, OrderedFood
from decimal import Decimal
import json


class PlaceOrderView(LoginRequiredMixin, FormView):
    login_url = 'login'
    template_name = 'orders/place_order.html'
    form_class = OrderForm

    # Helper function to convert Decimal to float
    def decimal_to_float(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def get_cart_data(self, cart_items):
        amounts = get_cart_amounts(self.request)
        return {
            'cart_items': cart_items,
            'subtotal': amounts['subtotal'],
            'total_tax': amounts['tax'],
            'grand_total': amounts['grand_total'],
            'tax_data': amounts['tax_dict'],
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
        # Convert Decimal to float for tax_dict
        tax_data = json.dumps(amounts['tax_dict'], default=self.decimal_to_float)

        order = Order.objects.create(
            user=self.request.user,
            total=amounts['grand_total'],
            tax_data=tax_data,
            total_tax=amounts['tax'],
            payment_method=self.request.POST['payment_method'],
            **form.cleaned_data
        )
        order.order_number = generate_order_number(order.id)
        order.save()  # Update order number
        return order


class PaymentsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'  # Redirect to login if not authenticated
    template_name = 'payments.html'  # Aapka payment page ka template

    def post(self, request, *args, **kwargs):
        # Check if the request is AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Retrieve Data from POST Request
            order_number = request.POST.get('order_number')
            transaction_id = request.POST.get('transaction_id')  # Static Transaction ID
            payment_method = request.POST.get('payment_method')
            status = request.POST.get('status')  # Static Status

            # Fetch the Order object
            try:
                order = Order.objects.get(user=request.user, order_number=order_number)
            except Order.DoesNotExist:
                return JsonResponse({'error': 'Order does not exist.'}, status=404)

            # Create Payment object and save it
            payment = self.create_payment(request.user, transaction_id, payment_method, order.total, status)
            
            # Update the Order with the payment details
            self.update_order(order, payment)

            # Move Cart items to OrderedFood model
            self.move_cart_to_ordered_food(request.user, order, payment)


            # Prepare response
            response = {
                'order_number': order_number,
                'transaction_id': transaction_id,
            }
            return JsonResponse(response)

        return JsonResponse({'error': 'Invalid request. This endpoint only accepts AJAX requests.'}, status=400)

    def create_payment(self, user, transaction_id, payment_method, amount, status):
        """Creates and saves a payment."""
        payment = Payment(
            user=user,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=amount,
            status=status
        )
        payment.save()
        return payment

    def update_order(self, order, payment):
        """Updates the order with payment details."""
        order.payment = payment
        order.is_ordered = True
        order.save()

    def move_cart_to_ordered_food(self, user, order, payment):
        """Moves cart items to OrderedFood model."""
        cart_items = Cart.objects.filter(user=user)
        for item in cart_items:
            OrderedFood.objects.create(
                order=order,
                payment=payment,
                user=user,
                fooditem=item.fooditem,
                quantity=item.quantity,
                price=item.fooditem.price,
                amount=item.fooditem.price * item.quantity
            )

