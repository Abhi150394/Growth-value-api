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
        # Example cutoff date check
        # if datetime.now() > settings.CUTOFF_DATE:
        #     return HttpResponseForbidden("Something went wrong", status=403)

        # Root path
        if str(request.path_info) == '/':
            return HttpResponse("Working")

        # Allow admin
        if str(request.path_info).startswith('/admin/'):
            return self.get_response(request)

        # Allow some URLs without check
        if request.path_info in ALLOWED_URL_LIST:
            return self.get_response(request)

        # Get DRF user
        drf_request: RestFrameworkRequest = APIView().initialize_request(request)
        user = drf_request.user

        # ✅ FIX: Handle AnonymousUser safely
        if user.is_authenticated:
            if getattr(user, "role", None) == "admin" or (
                request.path_info == f"/api/users/list/{user.id}/"
            ):
                return self.get_response(request)

            # Payment check
            check = checkPayment(user.id)
            paid = check.get("paid", False)
            payment_status = check.get("payment_status", False)
            if not (payment_status and paid):
                return HttpResponseForbidden("Payment Required")

        return self.get_response(request)


