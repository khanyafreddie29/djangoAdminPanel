from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Gig(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('pending_confirmation', 'Pending Confirmation'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    )

    CATEGORY_CHOICES = (
        ('errand', 'Errand'),
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('shopping', 'Shopping'),
        ('other', 'Other'),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gigs_as_client'
    )
    hustler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gigs_as_hustler',
        null=True, blank=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='open')
    completion_pin = models.CharField(max_length=255, blank=True, null=True)
    client_confirmed = models.BooleanField(default=False)
    hustler_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        status_changed = False

        if self.pk:
            try:
                old = Gig.objects.get(pk=self.pk)
                status_changed = old.status != self.status
            except Gig.DoesNotExist:
                status_changed = False

            if status_changed:
                self._pending_status_email = self.status

        super().save(*args, **kwargs)

        if hasattr(self, '_pending_status_email'):
            from notifications.tasks import queue_email

            if self._pending_status_email == 'accepted':
                # client gets told who accepted
                queue_email(
                    user_id=self.client.id,
                    event_type='gig_accepted_client',
                    context_data={
                        'gig_id': self.id,
                        'title': self.title,
                        'budget': str(self.budget),
                        'location': self.location,
                        'hustler_name': self.hustler.get_full_name() or self.hustler.username if self.hustler else 'A hustler',
                    }
                )
                # hustler gets told they accepted
                if self.hustler:
                    queue_email(
                        user_id=self.hustler.id,
                        event_type='gig_accepted_hustler',
                        context_data={
                            'gig_id': self.id,
                            'title': self.title,
                            'budget': str(self.budget),
                            'location': self.location,
                        }
                    )

            elif self._pending_status_email == 'in_progress':
                # only client gets notified, hustler started it themselves
                queue_email(
                    user_id=self.client.id,
                    event_type='gig_started',
                    context_data={
                        'gig_id': self.id,
                        'title': self.title,
                        'budget': str(self.budget),
                        'location': self.location,
                        'hustler_name': self.hustler.get_full_name() or self.hustler.username if self.hustler else 'A hustler',
                    }
                )

            elif self._pending_status_email == 'pending_confirmation':
                # client set this status themselves — only notify hustler
                if self.hustler:
                    queue_email(
                        user_id=self.hustler.id,
                        event_type='gig_pending_confirmation',
                        context_data={
                            'gig_id': self.id,
                            'title': self.title,
                            'budget': str(self.budget),
                            'location': self.location,
                            'status': self._pending_status_email,
                        }
                    )

            else:
                status_email_map = {
                    'completed': 'gig_completed',
                    'cancelled': 'gig_cancelled',
                    'disputed':  'gig_disputed',
                }
                event_type = status_email_map.get(self._pending_status_email)
                if event_type:
                    context_data = {
                        'gig_id': self.id,
                        'title': self.title,
                        'budget': str(self.budget),
                        'location': self.location,
                        'status': self._pending_status_email,
                    }
                    queue_email(
                        user_id=self.client.id,
                        event_type=event_type,
                        context_data=context_data
                    )
                    if self.hustler:
                        queue_email(
                            user_id=self.hustler.id,
                            event_type=event_type,
                            context_data=context_data
                        )

            del self._pending_status_email

    def __str__(self):
        return f"{self.title} - {self.status}"

    class Meta:
        ordering = ['-created_at']