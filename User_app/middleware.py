# middleware.py
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import datetime
from django.utils.deprecation import MiddlewareMixin
from .models import APICallLog  # Model we'll create later


class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = JWTAuthentication()
            try:
                auth.get_user(auth.get_validated_token(request.META['HTTP_AUTHORIZATION'].split(' ')[1]))
            except InvalidToken:
                return JsonResponse({'error': 'Invalid token'}, status=401)
        else:
            return JsonResponse({'error': 'Authorization header missing'}, status=401)
        
        response = self.get_response(request)
        return response




# middleware.py
from .models import APICallLog
from django.utils.timezone import now
from django.db.models import F

class APICallLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):  # Only log API calls
            today = now().date()
            endpoint = request.path
            log, created = APICallLog.objects.get_or_create(
                date=today,
                endpoint=endpoint,
                defaults={'count': 1}
            )
            if not created:
                log.count = F('count') + 1
                log.save()

        response = self.get_response(request)
        return response
