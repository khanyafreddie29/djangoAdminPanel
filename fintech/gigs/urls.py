# gigs/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import GigViewSet

router = SimpleRouter()
router.register(r'', GigViewSet, basename='gig')

urlpatterns = [
    path('', include(router.urls)),
]