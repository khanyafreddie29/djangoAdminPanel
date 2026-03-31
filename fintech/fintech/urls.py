"""
URL configuration for fintech project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django admin
    # directly manage database models, dev/superuse tool
    path('api-auth/', include('rest_framework.urls')),
    # drf built-in browser ui used to visually test the api endpoints during development
    
    # 2FA protected admin login
    path('', include(tf_urls)),
    
    # JWT token endpoints (ADD THESE)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/admin/', include('adminPanel.urls')),
    # this is the custom rest api for the admin panel built
    path('api/users/', include('users.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/disputes/', include('disputes.urls')),
    path('api/gigs/', include('gigs.urls')),
    
    # email notification
    path('api/notifications/', include('notifications.urls')),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
