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
import stripe
from django.conf import settings # new
from django.http.response import JsonResponse # new
from django.views.decorators.csrf import csrf_exempt # new
from django.utils.decorators import method_decorator
from django.views import View


from django.shortcuts import redirect

class PlaceOrderView(LoginRequiredMixin, FormView):
    login_url = 'login'
    template_name = 'orders/place_order.html'
    form_class = OrderForm

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

        context.update(self.get_cart_data(cart_items))
        return context

    def form_valid(self, form):
        cart_items = Cart.objects.filter(user=self.request.user)

        # Redirect to marketplace if the cart is empty
        if not cart_items.exists():
            return redirect('marketplace')

        order = self.create_order(form)
        return self.render_to_response(self.get_context_data(order=order))

    def create_order(self, form):
        amounts = get_cart_amounts(self.request)
        tax_data = json.dumps(amounts['tax_dict'], default=self.decimal_to_float)

        order = Order.objects.create(
            user=self.request.user,
            total=amounts['grand_total'],
            tax_data=tax_data,
            total_tax=amounts['tax'],
            payment_method=self.request.POST['payment_method'],
            vendor=self.get_vendor(),
            **form.cleaned_data
        )
        order.order_number = generate_order_number(order.id)
        order.save()

        cart_items = Cart.objects.filter(user=self.request.user)
        for item in cart_items:
            OrderedFood.objects.create(
                order=order,
                user=self.request.user,
                fooditem=item.fooditem,
                quantity=item.quantity,
                price=item.fooditem.price,
                amount=item.fooditem.price * item.quantity,
                vendor=item.fooditem.category.vendor
            )

        # Clear the cart after placing the order
        return order

    def get_vendor(self):
        cart_items = Cart.objects.filter(user=self.request.user)
        if cart_items.exists():
            return cart_items.first().fooditem.category.vendor
        return None

    

@method_decorator(csrf_exempt, name='dispatch')  
class StripeConfig(View):
    def get(self, request, *args, **kwargs):
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@method_decorator(csrf_exempt, name='dispatch')  
class CreateCheckoutSession(View):
    def get(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        domain_url = 'http://localhost:8000/'

        order_id = request.GET.get('order_id')
        
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                
                # Create line items from the ordered food items
                line_items = [{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.fooditem.food_title,
                        },
                        'unit_amount': int(item.price * 100),  # Convert price to cents for Stripe
                    },
                    'quantity': item.quantity,
                } for item in order.orderedfood_set.all()]  # Fetch all OrderedFood items for this order

                # Create Stripe checkout session
                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + 'orders/successed?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=domain_url + 'orders/cancelled/',
                    payment_method_types=['card'],
                    mode='payment',
                    line_items=line_items,
                    metadata={'order_id': order.id}
                )
                stripe_config['sessionId'] = checkout_session['id']
            except Order.DoesNotExist:
                return JsonResponse({'error': 'Order not found'}, status=404)
            except Exception as e:
                return JsonResponse({'error': 'General Error: ' + str(e)}, status=500)

        return JsonResponse(stripe_config, safe=False)


class SuccessView(TemplateView):
    template_name = 'success.html'


class CancelledView(TemplateView):
    template_name = 'cancelled.html'


@method_decorator(csrf_exempt, name='dispatch')
class StripeWeebhook(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        # Verify the webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
            )
        except ValueError as e:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        

        # Hanle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_successful_payment(session)
        
        return JsonResponse({'status': 'success'}, status=200)
    
    def handle_successful_payment(self, session):
        order_id = session.get('metadata', {}).get('order_id')
        

        # Retrieve payment intent and amount from the session
        payment_intent = session.get('payment_intent')
        amount = session.get('amount_total') / 100  # amount_total is in cents

        try:
            # Update the order in the database
            order = Order.objects.get(id=order_id)

            # Create a Payment record
            payment = Payment.objects.create(
                user=order.user,
                transaction_id=payment_intent,
                payment_method=order.payment_method,
                amount=amount,
                status='Completed',
            )

            # Assign the Payment instance to the order's payment field
            order.payment = payment  # Set the order's payment to the Payment instance
            order.is_ordered = True
            order.save()

            # update orderedfood 
            OrderedFood.objects.filter(order=order).update(payment=payment)

            # delete cart items 
            cart_items = Cart.objects.filter(user=order.user)
            cart_items.delete()

            print(f"Payment for Order ID {order_id} successfully recorded with transaction ID {payment_intent}.")
        except Order.DoesNotExist:
            print(f"Order with ID {order_id} does not exist.")
        except Exception as e:
            print(f"An error occurred while processing the payment: {str(e)}")
            
