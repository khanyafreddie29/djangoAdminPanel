# transactions/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters
from .models import Transaction
from .serializers import TransactionSerializer
from adminPanel.permissions import IsAdminOrSuperAdmin
from notifications.tasks import queue_email


class TransactionFilter(filters.FilterSet):
    """Filter transactions"""
    min_amount = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='amount', lookup_expr='lte')
    status = filters.ChoiceFilter(choices=Transaction.STATUS_CHOICES)

    class Meta:
        model = Transaction
        fields = ['status', 'user']


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'update_status'):
            return [IsAdminOrSuperAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ('client', 'hustler'):
            return Transaction.objects.filter(user=user)
        return Transaction.objects.all()

    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)
        # Fire payment_received email on transaction creation
        queue_email(
            user_id=self.request.user.id,
            event_type='payment_received',
            context_data={
                'reference': transaction.reference,
                'amount': str(transaction.amount),
                'status': transaction.status,
                'transaction_type': transaction.transaction_type,
            }
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Transactions cannot be deleted.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Admin only — update transaction status and notify user."""
        transaction = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Transaction.STATUS_CHOICES):
            return Response(
                {'error': f'Invalid status. Choices are: {list(dict(Transaction.STATUS_CHOICES).keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Model save() override handles the status change email automatically
        transaction.status = new_status
        transaction.save(update_fields=['status'])

        return Response({
            'status': f'Transaction updated to {new_status}',
            'transaction_id': transaction.id
        })
