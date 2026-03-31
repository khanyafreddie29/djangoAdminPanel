# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import EmailPreferenceViewSet, EmailLogViewSet, EmailTemplateViewSet

router = SimpleRouter()
router.register(r'preferences', EmailPreferenceViewSet, basename='preferences')
router.register(r'logs', EmailLogViewSet, basename='logs')
router.register(r'templates', EmailTemplateViewSet, basename='templates')

urlpatterns = [
    path('', include(router.urls)),
]