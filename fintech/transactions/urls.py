from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import TransactionViewSet

router = SimpleRouter()
router.register(r'', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]