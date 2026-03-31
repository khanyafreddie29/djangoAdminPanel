# gigs/ serializers.py

from rest_framework import serializers
from .models import Gig


class GigSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    hustler_email = serializers.EmailField(source='hustler.email', read_only=True)

    class Meta:
        model = Gig
        fields = [
            'id', 'title', 'description', 'budget', 'location', 'category',
            'status', 'client', 'client_email', 'hustler', 'hustler_email',
            'completion_pin', 'client_confirmed', 'hustler_confirmed',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'client', 'created_at', 'updated_at',
            'client_confirmed', 'hustler_confirmed'
        ]


class GigListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    client_email = serializers.EmailField(source='client.email', read_only=True)
    hustler_email = serializers.EmailField(source='hustler.email', read_only=True)

    class Meta:
        model = Gig
        fields = [
            'id', 'title', 'budget', 'status', 'category',
            'location', 'client_email', 'hustler_email', 'created_at'
        ]