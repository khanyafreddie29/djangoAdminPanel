# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction
import uuid


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'reference', 'transaction_type', 'amount', 'status',
            'description', 'user', 'user_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reference', 'user']

    def create(self, validated_data):
        # Auto-generate reference on creation
        validated_data['reference'] = str(uuid.uuid4())[:20]
        return super().create(validated_data)