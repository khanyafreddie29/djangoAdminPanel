# adminPanel/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from users.models import User
from transactions.models import Transaction
from disputes.models import Dispute
from .models import AdminAction
from .serializers import DashboardSerializer
from adminPanel.permissions import IsAdminOrSuperAdmin, IsAdminSupportOrAbove
from .utils import get_client_ip
from adminPanel.throttles import AdminActionThrottle
from gigs.models import Gig


class DashboardViewSet(viewsets.ViewSet):

    def get_permissions(self):
        return [IsAdminOrSuperAdmin()]

    def get_throttles(self):
        return [AdminActionThrottle()]

    def list(self, request):
        """Get dashboard metrics"""
        metrics = {
            'user_count': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'suspended_users': User.deleted_objects.count(),
            'client_count': User.objects.filter(user_type='client').count(),
            'hustler_count': User.objects.filter(user_type='hustler').count(),
            'transaction_volume': Transaction.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'transaction_count': Transaction.objects.count(),
            'open_gigs': Gig.objects.filter(status='open').count(),
            'completed_gigs': Gig.objects.filter(status='completed').count(),
            'disputed_gigs': Gig.objects.filter(status='disputed').count(),
            'open_disputes': Dispute.objects.filter(status='open').count(),
            'resolved_disputes': Dispute.objects.filter(
                status__in=['resolved_client', 'resolved_hustler']
            ).count(),
            'recent_activity': AdminAction.objects.select_related(
                'admin', 'target_user'
            ).order_by('-timestamp')[:10],
        }

        AdminAction.objects.create(
            admin=request.user,
            action_type='dashboard_view',
            description='Viewed dashboard metrics',
            ip_address=get_client_ip(request),
        )

        serializer = DashboardSerializer(metrics)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_stats(self, request):
        """Get user registrations over the last 7 days"""
        last_7_days = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = User.objects.filter(created_at__date=date).count()
            last_7_days.append({
                'date': date,
                'new_users': count
            })

        AdminAction.objects.create(
            admin=request.user,
            action_type='dashboard_view',
            description='Viewed user stats',
            ip_address=get_client_ip(request),
        )

        return Response(last_7_days)