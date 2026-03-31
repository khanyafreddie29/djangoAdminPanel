from rest_framework import serializers
from .models import EmailPreference, EmailLog, EmailTemplate

class EmailPreferenceSerializer(serializers.ModelSerializer):
    # serializer for user email preferences
    
    class Meta:
        model = EmailPreference
        fields = [
            'id',
            'marketing_emails',
            'unsubscribed',
            'unsubscribed_at',
            'new_transaction',
            'terms_accepted',
            'payment_received',
            'delivery_confirmed',
            'funds_released',
            'dispute_opened',
            'created_at',
            'updated_at',
        ]
        
        read_only_fields =[
            'id',
            'unsubscribed_at',
            'created_at',
            'updated_at',
            # transactional emails cannot be togggled by user
            'new_transaction',
            'terms_accepted',
            'payment_received',
            'delivery_confirmed',
            'funds_released',
            'dispute_opened',
        ]
        
class EmailLogSerializer(serializers.ModelSerializer):
    # serializer for email logs -- admin view only
    user_email = serializers.EmailField(source='user.email', read_only = True)
    
    class Meta:
        model = EmailLog
        fields = [
            'id',
            'user_email',
            'event_type',
            'recipient_email',
            'subject',
            'status',
            'retry_count',
            'max_retries',
            'error_message',
            'sent_at',
            'created_at'
        ]
        
        read_only_fields = fields
        
class EmailTemplateSerializer(serializers.ModelSerializer):
    # serializer for email templates -- admin only
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'event_type',
            'subject',
            'html_body',
            'plain_text_body',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]