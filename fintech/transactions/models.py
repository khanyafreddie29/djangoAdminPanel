# transactions/models.py
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Transaction(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('awaiting_seller_acceptance', 'Awaiting Seller Acceptance'),
        ('awaiting_payment', 'Awaiting Payment'),
        ('payment_processing', 'Payment Processing'),
        ('funded', 'Funded'),
        ('in_delivery', 'In Delivery'),
        ('buyer_confirmed', 'Buyer Confirmed'),
        ('released', 'Released'),
        ('dispute_open', 'Dispute Open'),
        ('dispute_resolved_refund', 'Dispute Resolved - Refund'),
        ('dispute_resolved_release', 'Dispute Resolved - Release'),
        ('cancelled', 'Cancelled'),
    )

    TRANSACTION_TYPE_CHOICES = (
        ('payment', 'Payment'),
        ('transfer', 'Transfer'),
        ('refund', 'Refund'),
    )

    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='payment'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions_as_buyer'
    )
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions_as_merchant',
        null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=40, choices=STATUS_CHOICES, default='draft'
    )
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.reference} - {self.amount}"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Transaction.objects.get(pk=self.pk)
                status_changed = old.status != self.status
            except Transaction.DoesNotExist:
                status_changed = False

            if status_changed:
                self._pending_status_email = self.status

        super().save(*args, **kwargs)

        if hasattr(self, '_pending_status_email'):
            from notifications.tasks import queue_email
            status_email_map = {
                'draft':                        'transaction_draft',
                'awaiting_seller_acceptance':   'awaiting_seller_acceptance',
                'awaiting_payment':             'awaiting_payment',
                'payment_processing':           'payment_processing',
                'funded':                       'transaction_funded',
                'in_delivery':                  'in_delivery',
                'buyer_confirmed':              'buyer_confirmed',
                'released':                     'funds_released',
                'cancelled':                    'transaction_cancelled',
                'dispute_resolved_refund':      'transaction_refunded',
                'dispute_resolved_release':     'transaction_completed',
            }
            event_type = status_email_map.get(self._pending_status_email)
            if event_type:
                queue_email(
                    user_id=self.user.id,
                    event_type=event_type,
                    context_data={
                        'reference': self.reference,
                        'amount': str(self.amount),
                        'status': self._pending_status_email,
                        'transaction_type': self.transaction_type,
                    }
                )
            del self._pending_status_email

    class Meta:
        ordering = ['-created_at']