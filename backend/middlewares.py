from datetime import datetime
from django.conf import settings

from .views import checkPayment
from rest_framework.request import Request as RestFrameworkRequest
from rest_framework.views import APIView
from django.http import HttpResponseForbidden, HttpResponse

ALLOWED_URL_LIST = [
    '/api/demo/',
    "/api/forget_password/",
    "/api/reset_password/",
    '/api/register/',
    '/api/token/', 
    '/api/token/refresh/', 
    '/api/plans/', 
    '/api/checkout/',
    '/api/success/', 
    '/api/subscription/change/'
]

class PaymentRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        # if datetime.now() > settings.CUTOFF_DATE:
        #     return HttpResponseForbidden("Something went wrong", status=403)
        
        if (str(request.path_info) == '/'):
            return HttpResponse("Working")
        
        if (str(request.path_info).startswith('/admin/')):
            return self.get_response(request)
        
        if (request.path_info in ALLOWED_URL_LIST):
            return self.get_response(request)
        
        drf_request: RestFrameworkRequest = APIView().initialize_request(request)
        user = drf_request.user

        if user.role == "admin" or (request.path_info in [f'/api/users/list/{user.id}/']):
            return self.get_response(request)
        
        check = checkPayment(user.id)
        paid = check['paid']
        payment_status = check['payment_status']
        if not(payment_status == True and paid == True):
            return HttpResponseForbidden("Payment Required")

        response = self.get_response(request)
        return response
