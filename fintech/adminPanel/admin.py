from django.contrib import admin
from .models import AdminAction

@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action_type', 'timestamp', 'target_user')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('admin__email', 'description')