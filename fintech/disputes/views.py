# disputes/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from .models import Dispute
from .serializers import DisputeSerializer
from adminPanel.permissions import IsAdminSupportOrAbove
from adminPanel.models import AdminAction
from adminPanel.utils import get_client_ip
from notifications.tasks import queue_email


class DisputeFilter(filters.FilterSet):
    """Filter disputes"""
    status = filters.ChoiceFilter(choices=Dispute.STATUS_CHOICES)
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')

    class Meta:
        model = Dispute
        fields = ['status', 'raised_by']


class DisputeViewSet(viewsets.ModelViewSet):
    serializer_class = DisputeSerializer
    filterset_class = DisputeFilter
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'resolve'):
            return [IsAdminSupportOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ('client', 'hustler'):
            return Dispute.objects.filter(raised_by=user)
        return Dispute.objects.all()

    def perform_create(self, serializer):
        dispute = serializer.save(raised_by=self.request.user)
        # Fire dispute opened email
        queue_email(
            user_id=dispute.raised_by.id,
            event_type='dispute_opened',
            context_data={
                'dispute_id': dispute.id,
                'reference': dispute.transaction.reference,
                'reason': dispute.reason,
                'status': dispute.status,
            }
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Disputes cannot be deleted.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['patch'])
    def resolve(self, request, pk=None):
        dispute = self.get_object()
        new_status = request.data.get('status')

        valid_statuses = ('under_review', 'resolved_client', 'resolved_hustler')
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Choices are: {list(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dispute.status = new_status
        dispute.resolved_by = request.user
        dispute.save()

        AdminAction.objects.create(
            admin=request.user,
            action_type='dispute_action',
            description=f'Set dispute {dispute.id} to {new_status}',
            ip_address=get_client_ip(request),
            target_user=dispute.raised_by,
        )

        return Response({'status': f'dispute updated to {new_status}'})