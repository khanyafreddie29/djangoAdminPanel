# adminPanel/throttles.py
from rest_framework.throttling import UserRateThrottle

class AdminActionThrottle(UserRateThrottle):
    """Rate limit specifically for admin actions like suspend, verify, activate"""
    scope = 'admin_actions'