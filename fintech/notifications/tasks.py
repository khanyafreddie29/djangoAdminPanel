# notifications/tasks.py
from django_q.tasks import async_task, schedule
from django_q.models import Schedule
from .services import send_email, retry_failed_email
from .models import EmailLog

def task_send_email(user_id, event_type, context_data=None):
    # async task to send an email
    from users.models import User
    try:
        user = User.objects.get(id=user_id)
        send_email(user, event_type, context_data)
        
    except User.DoesNotExist:
        pass
    
def task_retry_failed_emails():
    # peridotic task - retries all failed emails that havent hit max retries
    # schedule this to run every 10 minutes
    
    failed_logs = EmailLog.objects.filter(
        status = 'failed',
        retry_count__lt=3
    )
    for log in failed_logs:
        retry_failed_email(log.id)
        
def queue_email(user_id, event_type, context_data=None):
    # helper to queue an email task
    async_task(
        'notifications.tasks.task_send_email',
        user_id,
        event_type,
        context_data,
        task_name=f"{event_type}_{user_id}"
    )
        