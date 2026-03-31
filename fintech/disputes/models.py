# disputes/models.py
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Dispute(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved_client', 'Resolved Client'),
        ('resolved_hustler', 'Resolved Hustler'),
    )

    transaction = models.ForeignKey(
        'transactions.Transaction', on_delete=models.PROTECT
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_disputes'
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"Dispute {self.id} - {self.transaction.reference}"

    def save(self, *args, **kwargs):
        status_changed = False 
    
        if self.pk:
            try:
                old = Dispute.objects.get(pk=self.pk)
                status_changed = old.status != self.status
            except Dispute.DoesNotExist:
                status_changed = False

        if status_changed:
            self._pending_status_email = self.status

    # auto set resolved_at when status becomes resolved
        if self.status in ('resolved_client', 'resolved_hustler') and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()

        super().save(*args, **kwargs)

        if hasattr(self, '_pending_status_email'):
            from notifications.tasks import queue_email
            status_email_map = {
                'under_review':      'dispute_investigating',
                'resolved_client':   'dispute_resolved',
                'resolved_hustler':  'dispute_resolved',
            }
            event_type = status_email_map.get(self._pending_status_email)
            if event_type:
                queue_email(
                    user_id=self.raised_by.id,
                    event_type=event_type,
                    context_data={
                        'dispute_id': self.id,
                        'reference': self.transaction.reference,
                        'status': self._pending_status_email,
                        'reason': self.reason,
                    }
                )
            del self._pending_status_email