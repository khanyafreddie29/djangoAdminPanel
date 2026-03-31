# Create your models here.
# notifications/models.py
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class EmailTemplate(models.Model):
    """HTML email templates stored in DB for easy updates"""
    EVENT_TYPES = (
        ('terms_accepted', 'Terms Accepted'),
        ('account_verified', 'Account Verified'),
        ('payment_received', 'Payment Received'),
        ('transaction_pending', 'Transaction Pending'),
        ('transaction_completed', 'Transaction Completed'),
        ('transaction_failed', 'Transaction Failed'),
        ('transaction_refunded', 'Transaction Refunded'),
        ('dispute_opened', 'Dispute Opened'),
        ('dispute_investigating', 'Dispute Investigating'),
        ('dispute_resolved', 'Dispute Resolved'),
        ('delivery_confirmed', 'Delivery Confirmed'),
        ('funds_released', 'Funds Released'),
        ('gig_created', 'Gig Created'),
        ('gig_accepted_client', 'Gig Accepted - Client Notification'),
        ('gig_accepted_hustler', 'Gig Accepted - Hustler Notification'),
        ('gig_started_client', 'Gig Started - Client Notification'),
        ('gig_started_hustler', 'Gig Started - Hustler Notification'),
        ('gig_pending_confirmation', 'Gig Pending Confirmation'),
        ('gig_completed', 'Gig Completed'),
        ('gig_cancelled', 'Gig Cancelled'),
        ('gig_disputed', 'Gig Disputed'),
        
    )

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, unique=True)
    subject = models.CharField(max_length=255)
    html_body = models.TextField()
    plain_text_body = models.TextField(help_text='Fallback for email clients that do not support HTML')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.event_type} - {self.subject}"

    class Meta:
        ordering = ['event_type']


class EmailPreference(models.Model):
    """Per-user notification settings"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_preference'
    )
    # Transactional — always sent, cannot be unsubscribed
    new_transaction = models.BooleanField(default=True)
    terms_accepted = models.BooleanField(default=True)
    payment_received = models.BooleanField(default=True)
    delivery_confirmed = models.BooleanField(default=True)
    funds_released = models.BooleanField(default=True)
    dispute_opened = models.BooleanField(default=True)

    # Marketing — can be unsubscribed
    marketing_emails = models.BooleanField(default=True)
    unsubscribed = models.BooleanField(default=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} preferences"

    class Meta:
        ordering = ['user']


class EmailLog(models.Model):
    """Tracks every email sent, delivery status and retry count"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='email_logs'
    )
    event_type = models.CharField(max_length=50)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sendgrid_message_id = models.CharField(max_length=255, blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.recipient_email} - {self.event_type} - {self.status}"

    @property
    def can_retry(self):
        return self.retry_count < self.max_retries and self.status == 'failed'

    class Meta:
        ordering = ['-created_at']