# disputes/ urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import DisputeViewSet

router = SimpleRouter()
router.register(r'', DisputeViewSet, basename='dispute')

urlpatterns = [
    path('', include(router.urls)),
]