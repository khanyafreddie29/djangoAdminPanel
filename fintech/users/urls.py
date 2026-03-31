# users/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import UserViewSet, UserRegistrationViewSet

router = SimpleRouter()
router.register(r'', UserViewSet, basename='user')
router.register(r'auth', UserRegistrationViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]