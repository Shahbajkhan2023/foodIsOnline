from django.utils.deprecation import MiddlewareMixin
from django.template.response import TemplateResponse
from django.urls import resolve


class NoConditionMatchMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        current_view_name = resolve(request.path_info).url_name
        if current_view_name == 'search':
            keyword = request.GET.get('keyword', '').strip()
            address = request.GET.get('address', '').strip()
            
            
            if not keyword and not address:
                context = {
                    'vendors': [],  
                    'vendor_count': 0,  
                    'no_search_message': "Please enter a search keyword or location to find vendors."
                }
                return TemplateResponse(request, 'marketplace/listings.html', context)

       
        return None
