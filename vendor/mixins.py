from django.http import JsonResponse

class AjaxAuthenticationMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.headers.get('x-requested-with') != 'XMLHttpRequest':
            return JsonResponse({'status': 'failed', 'message': 'Invalid request'}, status=400)
        return super().dispatch(request, *args, **kwargs)