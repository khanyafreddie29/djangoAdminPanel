from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

class AdminAction(models.Model):
    """Track all admin actions for audit log"""
    ACTION_TYPES = (
        ('login', 'Login'),
        ('user_suspend', 'User Suspension'),
        ('user_activate', 'User Activation'),
        ('user_verify', 'User Verification'),
        ('transaction_view', 'Transaction View'),
        ('dispute_action', 'Dispute Action'),
        ('dashboard_view', 'Dashboard View'),
    )
    
    # Change both ForeignKeys
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='targeted_actions')
    
    # Track changes to this model too
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.admin.email} - {self.action_type} - {self.timestamp}"