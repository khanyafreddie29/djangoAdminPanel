# gigs/admin.py
from django.contrib import admin
from .models import Gig

@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'hustler', 'status', 'budget', 'category', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'client__email', 'hustler__email')