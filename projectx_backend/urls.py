from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls')),
    path('shopify/', include('shopify_integration.urls')),

    #lightspeed endpoints
    path("lightspeed/", include("lightspeed_integration.urls")),

]
