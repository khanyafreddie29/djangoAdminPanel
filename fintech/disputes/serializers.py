# disputes/ serializers.py
from rest_framework import serializers
from .models import Dispute

class DisputeSerializer(serializers.ModelSerializer):
    """Dispute serializer"""
    raised_by_email = serializers.EmailField(source='raised_by.email', read_only=True)
    transaction_reference = serializers.CharField(source='transaction.reference', read_only=True)
    
    class Meta:
        model = Dispute
        fields = ['id', 'transaction', 'transaction_reference', 'raised_by', 
                 'raised_by_email', 'reason', 'status', 'created_at', 
                 'updated_at', 'resolved_at', 'resolved_by']
        read_only_fields = ['created_at', 'updated_at', 'resolved_at', 'raised_by', 'resolved_by']