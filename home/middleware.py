import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied

logger = logging.getLogger('home.middleware')

class AdminIPRestrictorMiddleware:
    """
    Middleware that restricts access to the /admin/ path to specific IPs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            # In production, check against settings.ALLOWED_ADMIN_IPS
            # For this example, we log and allow localhost, or you can implement a strict check
            ip = self.get_client_ip(request)
            allowed_ips = getattr(settings, 'ALLOWED_ADMIN_IPS', ['127.0.0.1'])
            
            if ip not in allowed_ips and not settings.DEBUG:
                logger.warning(f"Unauthorized Admin Access Attempt from IP: {ip}")
                raise PermissionDenied("Access Restricted")
                
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
