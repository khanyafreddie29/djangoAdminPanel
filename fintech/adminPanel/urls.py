from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import DashboardViewSet

app_name = 'adminPanel'

router = SimpleRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]