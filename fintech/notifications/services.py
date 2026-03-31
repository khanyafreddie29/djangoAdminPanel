from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.template import Template, Context
from .models import EmailTemplate, EmailLog, EmailPreference

def get_or_create_preferences(user):
    # get or create email preferences for a user
    preference, created = EmailPreference.objects.get_or_create(user=user)
    return preference

def should_send_email(user, event_type):
    # check if email should be sent based on user preferences
    # transactional email always sends regardless of preferneces
    ALWAYS_END = (
        'new_transaction',
        'terms_accepted',
        'payments_received',
        'delivery_confirmed',
        'funds_released',
        'dispute_opened',
    )
    
    if event_type in ALWAYS_END:
        return True
    
    preference = get_or_create_preferences(user)
    
    # if fully unsubscribed, block marketing only
    if preference.unsubscribed and event_type == 'marketing':
        return False
    
    return getattr(preference, event_type, True)

def render_template(template_str, context_data):
    # render a django template string with context data
    template = Template(template_str)
    context = Context(context_data)
    return template.render(context)

def send_email(user, event_type, context_data=None):
    # core email sending function
    # creates an emaillog entry and sends via django email backend
    # returns the emaillog bro
    
    if context_data is None:
        context_data= {}
        
    # always add a user to context
    context_data['user'] = user
    
    # check preferences
    if not should_send_email(user, event_type):
        return None
    
    # get template
    try:
        template = EmailTemplate.objects.get(event_type=event_type, is_active=True)
    except EmailTemplate.DoesNotExist:
        # log the failture and return
        EmailLog.objects.create(
            user=user,
            event_type=event_type,
            recipient_email=user.email,
            subject='N/A',
            status='failed',
            error_message=f"No active template found for event: {event_type}",
        )
        
        return None
    
    # render subject and body with context
    subject = render_template(template.subject, context_data)
    html_body = render_template(template.html_body, context_data)
    plain_body = render_template(template.plain_text_body, context_data)
    
    # creating a log entry
    log = EmailLog.objects.create(
        user=user,
        event_type=event_type,
        recipient_email=user.email,
        subject=subject,
        status='pending',
    )
    
    # sending the email
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=None,
            to=[user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        
        # update log on success
        log.status = 'sent'
        log.sent_at = timezone.now()
        log.save(update_fields=['status','sent_at'])
        
    except Exception as e:
        # update log on failure
        log.status = 'failed'
        log.error_message = str(e)
        log.save(update_fields=['status', 'error_message'])
        
    return log

def retry_failed_email(log_id):
    # retry a failed email up to max_retries times.
    # called by django q task
    
    try:
        log = EmailLog.objects.get(id=log_id)
    except EmailLog.DoesNotExist:
        return
    
    if not log.can_retry:
        return
    
    # increment retry count:
    log.retry_count += 1
    log.status = 'retrying'
    log.save(update_fields=['retry_count', 'status'])
    
    try:
        template = EmailTemplate.objects.get(event_type=log.event_type, is_active=True)
        
        msg = EmailMultiAlternatives(
            subject=log.subject,
            body=template.plain_text_body,
            from_email=None,
            to=[log.recipient_email],
        )
        msg.attach_alternative(template.html_body, 'text/html')
        msg.send()
        
        log.status = 'sent'
        log.sent_at = timezone.now()
        log.save(update_fields=['status', 'sent_at'])
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save(update_fields=['status', 'error_message'])