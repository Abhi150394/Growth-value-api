from django.urls import include, path
from rest_framework import routers
from . import views
from .views import MyTokenObtainPairView, MyTokenRefreshView
from .views import ShipdayOrdersView,XMLUploadView


router = routers.DefaultRouter()
router.register(r'order', views.OrderViewSet)
router.register(r'wishlist', views.WishlistViewSet)
router.register(r'search', views.SearchViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
#path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
urlpatterns = [
    path('', include(router.urls)),

    path('dashboard/', views.DashboardView.as_view()),
    path('list/wishlist/', views.wish_list),
    path('list/scraper/', views.list_scrapers),

    path('admin/dashboard/', views.AdminDashboardView.as_view()),
    path('start/scraper/<int:id>/', views.start_scrape),

    path('demo/', views.DemoProductView.as_view(), name='demo_products'),
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    path('searchbar/', views.SearchProductView.as_view(), name='search_product'),

    path('check_otp/<int:otp>/', views.check_opt),

    path('plans/', views.PlanView.as_view()),
    path('checkout/', views.CheckoutView.as_view()),
    path('success/', views.SuccessfulView.as_view()),
    path('subscription/change/', views.ChangeSubscriptionView.as_view()),
    path('subscription/cancel/', views.CancelSubscriptionView.as_view()),

    path('forget_password/', views.SendForgetPasswordEmailAPIView.as_view(), name='forget-password'),
    path('reset_password/',views.ResetPasswordAPIView.as_view(), name="reset-passwoed"),
    path('register/', views.register),
    path('users/list/', views.list_users),
    path('users/<int:id>/', views.update_users),
    path('users/list/<int:id>/', views.get_user),
    path('vendors/', views.VendorsAPIView.as_view(), name="vendors"),
    path('users/delete/<int:id>/', views.delete_users),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path("shipday/orders/", ShipdayOrdersView.as_view(), name="shipday-orders"),
    path('upload-xml/', XMLUploadView.as_view(), name='upload-xml')
]