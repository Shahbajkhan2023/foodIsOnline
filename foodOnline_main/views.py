from django.views.generic import ListView
from vendor.models import Vendor


class Home(ListView):
    model = Vendor
    template_name = "home.html"
    context_object_name = "vendors"
    
    def get_queryset(self):
        return Vendor.objects.filter(is_approved=True, user__is_active=True)[:8]

