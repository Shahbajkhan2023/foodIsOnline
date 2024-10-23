import csv
import io
from django.core.management.base import BaseCommand
from orders.models import Order
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate vendor reports for orders created in the last minute'

    def handle(self):
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        orders = Order.objects.filter(created_at__gt=one_hour_ago)

        if not orders.exists():
            self.stdout.write(self.style.WARNING('No new orders found in the last minute.'))
            return

        vendor_report = {}
        for order in orders:
            vendor = order.vendor
            if vendor not in vendor_report:
                vendor_report[vendor] = []
            vendor_report[vendor].append(order)

        for vendor, orders in vendor_report.items():
            email_body = f"Hello {vendor.vendor_name},\n\nHere is your report for the last minute:\n"
            email_body += "\nPlease find the detailed report attached as a CSV file.\n"
            email_body += "\nBest regards,\nYour FoodIsOnline Team"

            
            csv_file = self._generate_csv(orders)
            self._send_email_with_attachment(vendor.user.email, 'Your Latest Order Report', email_body, csv_file)

        self.stdout.write(self.style.SUCCESS('Successfully generated vendor reports'))

    def _generate_csv(self, orders):
        """Helper function to generate CSV for the vendor's orders."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(['Order ID', 'Order Date', 'Order Total', 'Order Detail', 'Product', 'Quantity', 'Price'])

        # Write order details to CSV
        for order in orders:
            for order_detail in order.orderedfood_set.all():
                writer.writerow([
                    order.id,
                    order.created_at,
                    order.total,
                    order_detail.id,
                    order_detail.fooditem.food_title,
                    order_detail.quantity,
                    order_detail.price,
                ])

        buffer.seek(0)
        return buffer

    def _send_email_with_attachment(self, to_email, subject, body, csv_file):
        from django.core.mail import EmailMessage

        email = EmailMessage(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
        )
        email.attach('vendor_report.csv', csv_file.getvalue(), 'text/csv')
        email.send(fail_silently=False)
