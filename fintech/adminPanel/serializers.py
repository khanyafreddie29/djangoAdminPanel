# adminPanel/serializers.py
from rest_framework import serializers
from .models import AdminAction


class AdminActionSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    target_user_email = serializers.EmailField(source='target_user.email', read_only=True)

    class Meta:
        model = AdminAction
        fields = ['id', 'admin_email', 'action_type', 'description',
                  'ip_address', 'timestamp', 'target_user_email']


class DashboardSerializer(serializers.Serializer):
    user_count = serializers.IntegerField()
    active_users = serializers.IntegerField()
    suspended_users = serializers.IntegerField()
    client_count = serializers.IntegerField()
    hustler_count = serializers.IntegerField()
    open_gigs = serializers.IntegerField()
    completed_gigs = serializers.IntegerField()
    disputed_gigs = serializers.IntegerField()
    transaction_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = serializers.IntegerField()
    open_disputes = serializers.IntegerField()
    resolved_disputes = serializers.IntegerField()
    recent_activity = AdminActionSerializer(many=True)