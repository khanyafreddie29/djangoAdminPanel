# notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_q.tasks import async_task

from .models import EmailPreference, EmailLog, EmailTemplate
from .serializers import (
    EmailPreferenceSerializer,
    EmailLogSerializer,
    EmailTemplateSerializer,
)
from .services import get_or_create_preferences
from adminPanel.permissions import IsAdminOrSuperAdmin


class EmailPreferenceViewSet(viewsets.GenericViewSet):
    """
    Manage email preferences for the authenticated user.
    - GET /notifications/preferences/ — view preferences
    - PATCH /notifications/preferences/update/ — update preferences
    - POST /notifications/preferences/unsubscribe/ — unsubscribe from marketing
    - POST /notifications/preferences/resubscribe/ — resubscribe to marketing
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmailPreferenceSerializer

    def get_object(self):
        return get_or_create_preferences(self.request.user)

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's email preferences."""
        preference = self.get_object()
        serializer = EmailPreferenceSerializer(preference)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_preferences(self, request):
        """Update current user's email preferences."""
        preference = self.get_object()
        serializer = EmailPreferenceSerializer(
            preference, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe from marketing emails."""
        preference = self.get_object()

        if preference.unsubscribed:
            return Response(
                {'error': 'You are already unsubscribed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        preference.unsubscribed = True
        preference.marketing_emails = False
        preference.unsubscribed_at = timezone.now()
        preference.save(update_fields=[
            'unsubscribed', 'marketing_emails', 'unsubscribed_at'
        ])

        return Response({'status': 'Successfully unsubscribed from marketing emails.'})

    @action(detail=False, methods=['post'])
    def resubscribe(self, request):
        """Resubscribe to marketing emails."""
        preference = self.get_object()

        if not preference.unsubscribed:
            return Response(
                {'error': 'You are not unsubscribed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        preference.unsubscribed = False
        preference.marketing_emails = True
        preference.unsubscribed_at = None
        preference.save(update_fields=[
            'unsubscribed', 'marketing_emails', 'unsubscribed_at'
        ])

        return Response({'status': 'Successfully resubscribed to marketing emails.'})


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Email logs — admin only.
    - GET /notifications/logs/ — view all logs
    - GET /notifications/logs/{id}/ — view specific log
    - POST /notifications/logs/{id}/retry/ — manually retry a failed email
    """
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = EmailLogSerializer
    queryset = EmailLog.objects.all()

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Manually retry a failed email."""
        log = self.get_object()

        if not log.can_retry:
            return Response(
                {'error': 'Email cannot be retried. Either already sent or max retries reached.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        async_task(
            'notifications.tasks.retry_failed_email',
            log.id,
            task_name=f'retry_email_{log.id}',
        )

        return Response({'status': f'Retry queued for email log {log.id}.'})


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """
    Email templates — admin only.
    - GET /notifications/templates/ — list all templates
    - GET /notifications/templates/{id}/ — view specific template
    - POST /notifications/templates/ — create template
    - PATCH /notifications/templates/{id}/ — update template
    - POST /notifications/templates/{id}/preview/ — preview rendered template
    """
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = EmailTemplateSerializer
    queryset = EmailTemplate.objects.all()
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Preview a rendered email template with sample data."""
        template = self.get_object()

        sample_context = {
            'user': request.user,
            'amount': '500.00',
            'reference': 'TXN-SAMPLE-001',
            'status': 'completed',
            'dispute_id': '1',
            'reason': 'Sample dispute reason',
        }

        from .services import render_template
        rendered_html = render_template(template.html_body, sample_context)
        rendered_subject = render_template(template.subject, sample_context)
        rendered_plain = render_template(template.plain_text_body, sample_context)

        return Response({
            'subject': rendered_subject,
            'html_body': rendered_html,
            'plain_text_body': rendered_plain,
        })