import re
from datetime import datetime
import requests
from time import sleep
from rest_framework import viewsets
from django.db import connection

from backend.services.monthly_stats_builder import build_monthly_stats_response, build_product_item_stats_response
from backend.services.monthly_stats_sql import fetch_monthly_stats_raw, fetch_sales_productItem_raw
from .serializers import (
    UserSerializer, UserListSerializer, SearchSerializer, OrderSerializer, WishlistSerializer,
    ProductSerializer, ScraperSerializer, TagSerializer, VendorSerializer
    )
from .models import (
    UserData, Payment, Orders, Searches, Wishlist, Products, Scraper, Tag, Vendor,
    UserDataResetPassword
    )
from lightspeed_integration.models import LightspeedProduct
from django.db.models.functions import Trim
from backend.models import XMLFile
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework.decorators import api_view, permission_classes, authentication_classes

from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from backend.utils import (
    send_welcome_email, encode_base64, decode_base64, send_reset_password_email, validate_password, subscription_notif_email,
    )

from .scrape.main import call_scrape_snacksbosteels, call_scrape_bellimmo, call_scrape_givana, call_scrape_snacksdeal, call_scrape_frituurland, call_scrape_foodnl
import threading
import stripe
from projectx_backend.settings import SIMPLE_JWT
import jwt


import logging

import os
from dotenv import load_dotenv

from backend.permissions import IsAdminRole, IsOwnerOrAdmin, ADMIN_ROLES, BUSINESS_LEADER_ROLES, REGIONAL_MANAGER_ROLES

load_dotenv()  # loads variables from .env into environment

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
_logger = logging.getLogger(__name__)


stripe.api_key = STRIPE_API_KEY
# send forget password email view
@authentication_classes([])
@permission_classes([])
class SendForgetPasswordEmailAPIView(APIView):
    
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(f"User email required.", status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = UserData.objects.get(email=email, is_active=True)
            data = {"id":obj.id, "email":email}
            reset_token = encode_base64(data)
            current_time = timezone.now()
            valid_to = current_time + timedelta(hours=12)
            defaults = {
                "reset_token":reset_token,
                "valid_to": valid_to
            }
            userdata_resetpassword, created = UserDataResetPassword.objects.update_or_create(
                customer=obj,
                defaults=defaults
            )
            send_reset_password_email(
                user_name=obj.name,
                email_to=obj.email,
                token=reset_token,
            )
            return Response("Sent reset password email successfully!", status=status.HTTP_200_OK)
        except UserData.DoesNotExist as exc:
            _logger.error(f"error msg: {exc}")
            return Response(f"No account exists.", status=status.HTTP_400_BAD_REQUEST)

# reset password view
@authentication_classes([])
@permission_classes([])
class ResetPasswordAPIView(APIView):
    
    def post(self, request):
        token = request.data.get("token")
        data = decode_base64(token)
        reset_token = data.get("reset_token")
        new_pass = data.get("new_password")
        c_pass = data.get("confirm_password")
        if not new_pass==c_pass:
            return Response("Both password not matching", status=status.HTTP_400_BAD_REQUEST)
        
        is_valid = len(str(new_pass)) >= 8
        if is_valid is not True:
            return Response("Password must have 8 characters or more", status=status.HTTP_400_BAD_REQUEST)
            
        if not reset_token:
            return Response("Missing password reset token", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            now = timezone.now()
            reset_obj = UserDataResetPassword.objects.get(reset_token=reset_token, valid_to__gt=now)
            cus = reset_obj.customer
            cus.set_password(new_pass)
            cus.save()
            reset_obj.reset_token=None
            reset_obj.save()
            return Response("Password reset success!!", status=status.HTTP_200_OK)
        except UserDataResetPassword.DoesNotExist as exc:
            _logger.error(f"error msg: {exc}")
            return Response(f"Sorry, this link is expired.", status=status.HTTP_400_BAD_REQUEST)
            

# Categories API
####################################################################################

@authentication_classes([])
@permission_classes([])
class CategoriesView(APIView):
    
    def get(self, request):
        queryset = Tag.objects.all()
        data = TagSerializer(queryset, many=True).data
        return Response(data)


#User related APIs
####################################################################################
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register(request):
    try:
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = dict(serializer.data)
        data.pop('password')
        send_welcome_email(
            user_name=data.get("name"),
            email_to = data.get("email"),
        )
        return Response(data)
    except Exception as exc:
        _logger.error(f"Unable to register. error: {exc.args}")
        return Response(data={"error":exc.args}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminRole])
def list_users(request):
    queryset = UserData.objects.filter(is_deleted=False).order_by('id')
    serializer = UserListSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsOwnerOrAdmin])
def update_users(request, id):
    incoming = dict(request.data)
    admin_roles = {UserData.Roles.ADMIN, UserData.Roles.SUPERADMIN}
    if request.user.role not in admin_roles:
        incoming.pop('role', None)

    try:
        instance = UserData.objects.filter(is_deleted=False).get(id=id)
    except Exception as ex:
        return Response(str(ex), status=status.HTTP_404_NOT_FOUND)
    serializer = UserSerializer(instance, data=incoming, many=isinstance(incoming, list),
                        partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    data = dict(serializer.data)
    data.pop('password')
    return Response(data)

@api_view(['GET'])
@permission_classes([IsOwnerOrAdmin])
def get_user(request, id):
    try:
        instance = UserData.objects.filter(is_deleted=False).get(id=id)
        serializer = UserListSerializer(instance)
        response = serializer.data
    except:
        response = {"detail":"User not found"}
    return Response(response)

@api_view(['GET'])
@permission_classes([IsAdminRole])
def delete_users(request, id):
    try:
        data = UserData.objects.get(id=id)
        data.is_deleted = True
        data.save()
        response = "User Deleted Successfully!"
    except Exception as ex:
        response = str(ex)
    
    return Response({"detail":response})

def checkPayment(user_id):
    user = UserData.objects.get(id=user_id)
    
    # Exempt admin, superadmin, business leader, and regional manager from payment checks
    if user.role in ADMIN_ROLES | {UserData.Roles.BUSINESS_LEADER, UserData.Roles.REGIONAL_MANAGER}:
        return {"paid":True, "payment_status":True}
    
    customer_id = user.customer_id

    try:
        customers = stripe.Subscription.list(customer=customer_id)
        status = customers.data[0].status
        user.paid = True
        user.save()
    except Exception as ex:
        # intenntially make all false true for testing purpose
        user.paid = False            #False
        user.payment_status = False  #False
        user.save()
        return {"paid": False, "payment_status": False}       #False
    
    if status == "active" or status == "trialing" or status == "canceled":
        user.payment_status = True
        user.save()
        return {"paid":True, "payment_status":True}
    else:
        user.payment_status = False
        user.save()
        return {"paid":True, "payment_status":False}
class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        userid = jwt.decode(data['refresh'], SIMPLE_JWT['SIGNING_KEY'], algorithms=SIMPLE_JWT['ALGORITHM'], options={"verify_signature": False, "verify_exp": False})['user_id']
        status = checkPayment(userid)
        data.update(status)

        return data

class MyTokenRefreshView(TokenRefreshView):
    serializer_class = MyTokenRefreshSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)

        data.update(
                {'id': self.user.id})
        data.update({'username': self.user.email})
        try:
            data.update(
                {'role': self.user.role})
        except:
            data.update({'role': 'none'})

        status = checkPayment(self.user.id)
        data.update(status)

        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

@api_view(['GET'])
def check_opt(request, otp):
    data = {"detail":"OTP is verified!"}
    return Response(data)

#Payment related APIs
####################################################################################
class PlanView(APIView):
    def get(self, request):
        plans = stripe.Product.list(limit=5)
        res = []
        for p in plans:
            price = stripe.Price.retrieve(p['default_price'])
            formatted_date = ''
            try:
                customers = stripe.Subscription.list(customer=request.user.customer_id)
                price_selected = customers.data[0]['items']['data'][0]['plan']['id']
                timestamp = customers.data[0]['current_period_end']
                dt_object = datetime.datetime.fromtimestamp(timestamp)
                formatted_date = dt_object.strftime('%Y-%m-%d')
            except Exception as ex:
                price_selected = ''
            selected = False
            if p['default_price'] == price_selected:
                selected = True

            res.append({
                "price_id":p['default_price'],
                "price":price['unit_amount']/100,
                "interval":price.recurring.interval,
                "interval_count": price.recurring.interval_count,
                "currency":price['currency'],
                "name":p['name'],
                "description":p['description'],
                "selected":selected,
                'next_date':formatted_date
                }
            )

        return Response(res)

class CheckoutView(APIView):
    def post(self, request):
        price = request.data.get('price_id', ' ')

        try:
            session = stripe.checkout.Session.create(
                ui_mode = 'embedded',
                line_items=[
                    {
                        'price': price,
                        'quantity': 1,
                    },
                ],
                # subscription_data={
                #     "trial_settings": {"end_behavior": {"missing_payment_method": "cancel"}},
                #     "trial_period_days": 5,
                # },
                payment_method_collection="always",
                customer_email=request.user.email,
                
                mode='subscription',
                return_url= settings.GROWTH_VALUE_BASE_URL + '/success/{CHECKOUT_SESSION_ID}',
            )
        except Exception as ex:
            _logger.error(f"Unable to create checkout session. error_msg: {ex}")
            return Response('Invalid Session Creation!', status=status.HTTP_400_BAD_REQUEST)

        res = {"client_secret": session.client_secret}
    
        return Response(res)

class SuccessfulView(APIView):
    def post(self, request):
        plan = ""
        checkout = request.data.get('checkout_id', ' ')
        
        try:
            session = stripe.checkout.Session.retrieve(checkout)
        except Exception as ex:
            print(ex)
            return Response('Invalid Checkout Id!', status=status.HTTP_400_BAD_REQUEST)

        if session.payment_status == "paid":
            user = UserData.objects.get(id=request.user.id)
            user.paid = True
            user.save()
            email = user.email
            customers = stripe.Customer.list(email=email)
            if customers['data']:
                customer_id = customers['data'][0]['id']
                user.customer_id = customer_id
                user.save()
            else:
                print(f"No customer found with email: {email}")

            statuss = ''

            while not(statuss == 'active' or statuss == 'trialing'):
                try:
                    customers = stripe.Subscription.list(customer=customer_id)
                    statuss = customers.data[0].status
                except:
                    sleep(1)
            
            try:
                plan = customers.data[0]['plan']['interval'].title()
                # send subscription email notif
                subscription_notif_email(
                user_name = user.name,
                email_to = user.email,
                plan = plan,
            )
            except Exception as exc:
                _logger.error(f"Can't get subscription plan. error msg:{exc}")
            
            return Response("Payment Successful!")
        
        else:
            user = UserData.objects.get(id=request.user.id)
            user.paid = False
            user.save()
        
        return Response("Payment Unsuccessful", status=status.HTTP_402_PAYMENT_REQUIRED)

class ChangeSubscriptionView(APIView):
    def post(self, request):
        new_plan_id = request.data.get('price_id', ' ')
        customers = stripe.Subscription.list(customer=request.user.customer_id)
        try:
            sub_id = customers.data[0].id
        except:
            stripe.Subscription.create(
            customer=request.user.customer_id,
            items=[{"price": new_plan_id}],
            )
            return Response("Subscription Created Successfully!")

        try:
            subscription = stripe.Subscription.modify(sub_id, items=[{"id":customers.data[0]['items']['data'][0]['id'],
                "price": new_plan_id}])
        except Exception as ex:
            print(ex)
            return Response("Plan Change Failed!", status=status.HTTP_400_BAD_REQUEST)
        
        return Response("Plan Change Successfully!")

class CancelSubscriptionView(APIView):
    def post(self, request):
        customers = stripe.Subscription.list(customer=request.user.customer_id)
        sub_id = customers.data[0].id
        try:
            stripe.Subscription.cancel(sub_id, prorate=True, invoice_now=True)
        except:
            return Response("Cancel Failed", status=status.HTTP_400_BAD_REQUEST)
        
        stripe.Customer.delete(request.user.customer_id)

        return Response("Subscription Canceled!")

#General Application related APIs
####################################################################################

#Class based APIs
class OrderViewSet(viewsets.ViewSet):
    queryset = Orders.objects.filter(is_deleted=False).order_by('id')
    # serializer_class = OrderSerializer
    # http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def list(self, request):
        user = request.user.id
        vendors = request.query_params.get("vendor","")
        
        context = {
            'exclude_fields': [
                'is_deleted'
            ]
        }
        queryset = Orders.objects.filter(is_deleted=False).filter(user_id=user).order_by(
            'id')
        
        if vendors:
            vendor_list = vendors.split(",")
            queryset = queryset.filter(vendor__in=vendor_list)
        
        serializer = OrderSerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        context = {
            'exclude_fields': [
                'is_deleted'
            ]
        }
        queryset = Orders.objects.filter(is_deleted=False).filter(
            pk=pk)
        serializer = OrderSerializer(queryset, many=True, context=context)
        try:
            response = serializer.data[0]
        except:
            response = {"detail": "Not found."}
        return Response(response)
    
    def create(self, request):
        request.data['user_id'] = request.user.id
        # serializer = self.get_serializer(data=request.data)
        serializer  = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        response = serializer.data
        return Response(response)
    
    def delete(self, request):
        user = request.user.id
        pk = request.data.get("id") or request.data.get("pk")
        if pk is None:
            # Mark all orders for the user as deleted
            Orders.objects.filter(user_id=user, is_deleted=False).update(is_deleted=True)
            return Response(status=status.HTTP_200_OK)
        else:
            try:
                # Get the specific order by primary key (pk)
                Orders.objects.filter(pk=pk, user_id=user, is_deleted=False).update(
                    is_deleted=True
                )
                
                return Response(status=status.HTTP_200_OK)
            except Orders.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.filter(is_deleted=False).order_by('id')
    serializer_class = WishlistSerializer
    http_method_names = ['patch', 'post', 'delete']
    
    def create(self, request):
        user_id = request.user.id
        product_id = request.data.get('product')
        existing_wishlist_item= self.queryset.filter(user_id=user_id, product_id=product_id).first()
        if existing_wishlist_item:
            serializer = self.get_serializer(existing_wishlist_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        request.data['user_id'] = user_id
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        response = serializer.data
        return Response(response)
    
    def destroy(self, request, pk=None):
        qs = Wishlist.objects.filter(user_id=request.user, product__id=pk)
        if qs:
            qs.update(is_deleted=True)

        return Response(data={},status=status.HTTP_200_OK)
    
class SearchViewSet(viewsets.ModelViewSet):
    queryset = Searches.objects.filter(is_deleted=False).order_by('id')
    serializer_class = SearchSerializer
    http_method_names = ['post']
    
    def create(self, request):
        request.data['user_id'] = request.user.id
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        response = serializer.data
        return Response(response)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 50000

class DashboardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50000

class SearchProductView(APIView):
    def post(self, request):
        search_keyword = request.data.get('search')
        try:
            brandFilter = list(request.data.get('brand'))
        except:
            brandFilter = None
        try:
            vendorFilter = list(request.data.get('vendor'))
        except:
            vendorFilter = None
        user = UserData.objects.get(id=request.user.id)
        products = Products.objects.filter(is_deleted=False).exclude(brand__in=["","None"]).order_by("product_name","vendor")
        search = search_keyword.split(',') if search_keyword else ""
        for term in search:
            pattern = r'\b{}\b'.format(re.escape(term))
            products = products.filter(product_name__iregex=pattern)
        
        if brandFilter:
            if len(brandFilter) > 0:
                products = products.filter(brand__in=brandFilter)

        if vendorFilter:
            if len(vendorFilter) > 0:
                products = products.filter(vendor__in=vendorFilter)

        unique_brands = sorted(list(products.order_by().values_list('brand', flat=True).distinct()))
        if "None" in unique_brands:
            unique_brands.remove("None")
        unique_vendors = sorted(list(products.order_by().values_list('vendor', flat=True).distinct()))
        saved_products = user.saved_product_ids()
        paginator = StandardResultsSetPagination()
        paginated_data = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(paginated_data, many=True)
        if search_keyword.strip():
            searches_instance = Searches.objects.create(user_id=user, search=search_keyword, results=products.count())

        response_data = {
            'results': serializer.data,
            'count': products.count(),
            'brands': unique_brands,
            'vendors': unique_vendors,
            'saved_products': saved_products,
        }
        return paginator.get_paginated_response(response_data)
    
    def get(self, request):
        user = request.user
        products = Products.objects.filter(is_deleted=False).exclude(brand__in=["","None"]).order_by("product_name","vendor")
        unique_brands = sorted(list(products.order_by().values_list('brand', flat=True).distinct()))
        if "None" in unique_brands:
            unique_brands.remove("None")
        unique_vendors = sorted(list(products.order_by().values_list('vendor', flat=True).distinct()))
        saved_products = user.saved_product_ids()
        paginator = StandardResultsSetPagination()
        paginated_data = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(paginated_data, many=True)
        
        response_data = {
            'results': serializer.data,
            'count': products.count(),
            'brands':unique_brands,
            'vendors':unique_vendors,
            'saved_products': saved_products,
        }
        return paginator.get_paginated_response(response_data)

class DemoProductView(APIView):
    
    def get(self, request):
        products = Products.objects.filter(is_deleted=False)
        if len(products) > 8:
            products = products[:8]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        search_keyword = request.data.get("search")
        search = search_keyword.split(',')
        query = Q()
        for term in search:
            query |= Q(product_name__icontains=term.strip())
        products = Products.objects.filter(is_deleted=False).filter(query).order_by('product_name')
        if len(products) > 8:
            products = products[:8]
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class VendorsAPIView(APIView):
    
    def get(self, request):
        queryset = Vendor.objects.all()
        data = VendorSerializer(queryset, many=True).data
        return Response(data)

class DashboardView(APIView):
    def get(self, request):
        user = request.user.id
        order_count = Orders.objects.filter(is_deleted=False).filter(user_id=user).count()
        hours = order_count * 0.75
        dollars = f"${int(hours * 0.8)}"

        search = Searches.objects.filter(is_deleted=False).filter(user_id=user).order_by('-id')
        paginator = DashboardResultsSetPagination()
        paginated_data = paginator.paginate_queryset(search, request)
        
        data = SearchSerializer(instance=paginated_data, many=True)
        
        response_data = {"orders":order_count, "hours":hours, "saved":dollars, "searches":data.data}
        return paginator.get_paginated_response(response_data)

class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        subscriptions = stripe.Subscription.list()
        user_qs = UserData.objects.filter(is_deleted=False).prefetch_related("tags", "vendors")
        tabs = {'users':user_qs.count()}
        tabs['totalSubscriptions'] = len(subscriptions.data)
        table = []
        total_price = 0
        for i in subscriptions.data:
            customer = stripe.Customer.retrieve(str(i['customer'])).email
            uc = user_qs.filter(email=customer).first()
            tags, vendors = None, None
            if uc:
                tags = uc.tags.all()
                vendors = uc.vendors.all()
            duration = i['items']['data'][0]['plan']['interval']
            product = stripe.Product.retrieve(i['items']['data'][0]['plan']['product'])
            type = product['name']
            total_price = total_price + (i['items']['data'][0]['plan']['amount']/100)
            resp = {
                'user':customer,
                'type':type, 
                'status':i['status'],
                'duration':duration,
                "tags": [],
                "vendors": []
            }
            if tags:
                resp["tags"]= [t.name for t in uc.tags.iterator()]
            if vendors:
                resp["vendors"]= [v.name for v in uc.vendors.iterator()]
            
            table.append(resp)
        
        tabs['subscriptionAmount'] = total_price
        return Response({'tabs':tabs,'table':table})

#Funtion Based APIs
@api_view(['GET'])
def wish_list(request):
    user = request.user.id
    wish = Wishlist.objects.filter(is_deleted=False).filter(user_id=user).all().order_by("product__product_name","product__vendor")
    data = []
    for i in wish:
        data.append({"id":i.id, "product_id":i.product.id,"product_name": i.product.product_name,"link":i.product.link, "image_link":i.product.image_link, "price": i.product.price, "relative_price":i.product.relative_price,"vendor": i.product.vendor, "brand":i.product.brand})
    
    return Response(data)

# @api_view(['POST'])
# def search(request):
#     search = request.data['search']
#     user = UserData.objects.get(id=request.user.id)

#     products = Products.objects.filter(is_deleted=False).filter(Q(product_name__contains=search))

#     Searches.objects.create(user_id=user, search=search, results=products.count()).save()

#     data = ProductSerializer(instance=products, many=True)
#     return Response(data.data)

@api_view(['GET'])
@permission_classes([IsAdminRole])
def list_scrapers(request):
    scraper = Scraper.objects.filter(is_deleted=False)
    data = ScraperSerializer(instance=scraper, many=True)
    return Response(data.data)


@api_view(['GET'])
@permission_classes([IsAdminRole])
def start_scrape(request, id):
    try:
        if id == 1:
            thread = threading.Thread(target=call_scrape_snacksbosteels)
            thread.start()
        elif id == 2:
            thread = threading.Thread(target=call_scrape_bellimmo)
            thread.start()
        elif id == 3:
            thread = threading.Thread(target=call_scrape_givana)
            thread.start()
        elif id == 4:
            thread = threading.Thread(target=call_scrape_snacksdeal)
            thread.start()
        elif id == 5:
            thread = threading.Thread(target=call_scrape_frituurland)
            thread.start()
        elif id == 6:
            thread = threading.Thread(target=call_scrape_foodnl)
            thread.start()
        else:
            return Response({'message': 'Scraper not found!'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        _logger.error(f"Unable to scrap. Error: {exc}")
        return Response({'message': 'Something went wrong.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'Scrape Started'}, status=status.HTTP_202_ACCEPTED)



class ShipdayOrdersView(APIView):
    def get(self, request):
        location = request.GET.get("location") or "Frietchalet"
        headers = {
            "Authorization": settings.SHIPDAY_AUTH_HEADER_CREDENTIALS[location],
            # "PARTNER-API-KEY": settings.SHIPDAY_AUTH_HEADER_CREDENTIALS[location],
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(f"{settings.SHIPDAY_API_URL}orders", headers=headers)
            response.raise_for_status()  # raise error if request failed
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=500)

class ShipdayOrdersDetailsView(APIView):
    def get(self, request,ordernumber):
        location = request.GET.get("location") or "Frietchalet"
        
        headers = {
            "Authorization": settings.SHIPDAY_AUTH_HEADER_CREDENTIALS[location],
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(f"{settings.SHIPDAY_API_URL}orders/{ordernumber}", headers=headers)
            response.raise_for_status()  # raise error if request failed
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=500)



def _get_shyfter_headers(location: str = "Frietchalet") -> dict:
    """
    Build Shyfter headers for the given location.

    Supports both:
      - New per-location credentials via SHYFTER_AUTHORIZATION_CREDENTIALS (mapping)
      - Old single-token setup via SHYFTER_AUTHORIZATION_TOKEN (backward compatible)

    Expected SHYFTER_AUTHORIZATION_CREDENTIALS structure (per location):
        {
            "Frietchalet": {
                "token": "<bearer_token>",
                "department": "<department_id>"
            },
            "Tipzakske": { ... },
            "Frietbooster": { ... }
        }

    If a location is missing or credentials are incomplete, this safely falls
    back to the legacy env values.
    """
    default_department = "zVJk0KP2O45e3LZO"
    token = getattr(settings, "SHYFTER_AUTHORIZATION_TOKEN", None)
    department = default_department

    creds_by_location = getattr(settings, "SHYFTER_AUTHORIZATION_CREDENTIALS", None)
    if isinstance(creds_by_location, dict):
        creds = creds_by_location.get(location)
        if isinstance(creds, dict):
            token = creds.get("token") or token
            department = creds.get("Shyfter-Department") or default_department
        elif isinstance(creds, str):
            # If value is just a token string, keep default department
            token = creds or token

    headers = {
        "Accept": "application/json",
        "Shyfter-Department": department,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


class ShyfterEmployeesView(APIView):
    def get(self, request):
        location = request.GET.get("location") or "Frietchalet"
        headers = _get_shyfter_headers(location)

        all_employees = []
        next_url = f"{settings.SHYFTER_API_URL}/employees"  # first page URL

        try:
            while next_url:  # keep fetching until 'next' is null
                res = requests.get(next_url, headers=headers)
                res.raise_for_status()
                data = res.json()

                # append current page data
                all_employees.extend(data.get("data", []))

                # update next_url for next iteration
                next_url = data.get("links", {}).get("next")  

            return Response({"employees": all_employees}, status=200)

        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=500)


class ShyfterEmployeeClockingsView(APIView):
    def get(self, request, employee_id):
        location = request.GET.get("location") or "Frietchalet"
        headers = _get_shyfter_headers(location)

        try:
            url = f"{settings.SHYFTER_API_URL}/employees/{employee_id}/clockings"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return Response(response.json(), status=response.status_code)

        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=500)


class ShyfterEmployeeShiftsView(APIView):
    def get(self, request, employee_id):
        location = request.GET.get("location") or "Frietchalet"
        headers = _get_shyfter_headers(location)

        try:
            url = f"{settings.SHYFTER_API_URL}/employees/{employee_id}/shifts"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return Response(response.json(), status=response.status_code)

        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=500)


class XMLUploadView(APIView):
    def post(self, request, *args, **kwargs):
        xml_file = request.FILES.get('file')
        if not xml_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Create a new filename based on date
        today_str = datetime.now().strftime("%Y-%m-%d")
        new_filename = f"dayreport-{today_str}.xml"

        # ✅ Read file content (optional)
        xml_content = xml_file.read().decode('utf-8')

        # ✅ Reset file pointer (so Django can re-read it)
        xml_file.seek(0)

        # ✅ Save to database (FileField will handle upload path)
        xml_record = XMLFile.objects.create(
            file=xml_file,
            filename=new_filename,
            content=xml_content
        )

        # ✅ Optionally rename the actual stored file
        xml_record.file.name = f"xml_uploads/{new_filename}"
        xml_record.save()

        return Response(
            {
                'message': 'File uploaded successfully!',
                'filename': xml_record.filename,
                'path': xml_record.file.url if xml_record.file else None
            },
            status=status.HTTP_201_CREATED
        )
        
        
# ========================================Reports=====================================================================

@api_view(["GET"])
@permission_classes([IsAdminRole])
def lightspeed_sales_area(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        return Response({"error": "start_date and end_date are required"}, status=400)

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 🔹 1. Fetch raw flat data (UNCHANGED SQL)
    raw_data = fetch_monthly_stats_raw(
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    # 🔹 2. Build frontend response shape
    response = build_monthly_stats_response(
        raw_data=raw_data,
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return Response(response)

# ======================Sales Location =========================
@api_view(["GET"])
@permission_classes([IsAdminRole])
def lightspeed_sales_location(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        return Response({"error": "start_date and end_date are required"}, status=400)

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 🔹 1. Fetch raw flat data (UNCHANGED SQL)
    raw_data = fetch_monthly_stats_raw(
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    # 🔹 2. Build frontend response shape
    response = build_monthly_stats_response(
        raw_data=raw_data,
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return Response(response)

# ======================Sales Product Items =========================
@api_view(["GET"])
@permission_classes([IsAdminRole])
def lightspeed_sales_productItem(request):
    start_date=request.GET.get("start_date")
    end_date=request.GET.get("end_date")
    
    if not start_date or not end_date:
        return Response({"error":"start date and end date are required"},status=400)
    
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # 🔹 1. Fetch raw flat data (UNCHANGED SQL)
    raw_data = fetch_sales_productItem_raw(
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    # 🔹 2. Build frontend response shape
    response = build_product_item_stats_response(
        raw_data=raw_data,
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return Response(response)

@api_view(["GET"])
@permission_classes([IsAdminRole])
def lightspeed_product_Items(request):
    """
    Returns all distinct product names from lightspeed_products table.
    Equivalent SQL:
    SELECT DISTINCT TRIM(name) FROM lightspeed_products WHERE name IS NOT NULL;
    """

    try:
        product_names = (
            LightspeedProduct.objects
            .exclude(Q(name__isnull=True) | Q(name=""))
            .annotate(name_clean=Trim("name"))
            .values_list("name_clean", flat=True)
            .distinct()
            .order_by("name_clean")
        )

        return Response(
            {
                "count": len(product_names),
                "results": list(product_names)
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "error": "Failed to fetch product names",
                "details": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )