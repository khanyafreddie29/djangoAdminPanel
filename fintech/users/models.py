# users/models.py
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from safedelete.models import SafeDeleteModel, SafeDeleteManager
from safedelete.models import SOFT_DELETE
from simple_history.models import HistoricalRecords
from safedelete.managers import SafeDeleteAllManager


class UserManager(SafeDeleteManager, DjangoUserManager):
    """Custom manager that supports both soft delete and Django auth"""
    pass


class User(SafeDeleteModel, AbstractUser):
    """Custom User model with soft delete"""
    _safedelete_policy = SOFT_DELETE

    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('hustler', 'Hustler'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='client')
    phone_number = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    all_objects = SafeDeleteAllManager()
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.email} - {self.user_type}"

    def save(self, *args, **kwargs):
        if self.is_superuser and self.user_type == 'client':
            self.user_type = 'admin'
        if not kwargs.get('update_fields'):
            if self.password and not self.password.startswith(
                ('pbkdf2_sha256$', 'bcrypt$', 'argon2')
            ):
                self.set_password(self.password)
        super().save(*args, **kwargs)

    def suspend(self):
        """Suspend user — sets inactive AND soft deletes"""
        self.is_active = False
        self.save(update_fields=['is_active'])
        self.delete()

    def activate(self):
        """Reactivate suspended user"""
        try:
            self.undelete()
            self.is_active = True
            self.save(update_fields=['is_active'])
        except AssertionError:
            self.is_active = True
            self.save(update_fields=['is_active'])

    class Meta:
        permissions = [
            ("can_view_users", "Can view users"),
            ("can_suspend_users", "Can suspend users"),
            ("can_verify_users", "Can verify users"),
        ]