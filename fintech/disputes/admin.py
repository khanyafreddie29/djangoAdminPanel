# disputes/ admin.py
from django.contrib import admin
from .models import Dispute

@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'raised_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('transaction__reference', 'raised_by__email')