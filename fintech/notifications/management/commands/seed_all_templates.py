from django.core.management.base import BaseCommand
from notifications.models import EmailTemplate


def base_template(badge_color_bg, badge_color_text, badge_label, heading, body, details):
    return f"""<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;border-radius:8px;overflow:hidden;border:1px solid #ddd;">
  <tr>
    <td style="background:#1a1a2e;padding:24px 32px;">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:36px;height:36px;background:#f0c040;border-radius:6px;text-align:center;vertical-align:middle;font-weight:700;font-size:16px;color:#1a1a2e;">E</td>
          <td style="padding-left:12px;color:#ffffff;font-size:20px;font-weight:600;letter-spacing:0.5px;">EscrowShield</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td style="background:#ffffff;padding:32px;">
      <div style="display:inline-block;background:{badge_color_bg};color:{badge_color_text};font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;margin-bottom:20px;letter-spacing:0.5px;text-transform:uppercase;">{badge_label}</div>
      <h2 style="color:#1a1a2e;font-size:22px;font-weight:600;margin:0 0 12px;">{heading}</h2>
      <p style="color:#444;font-size:15px;line-height:1.6;margin:0 0 24px;">{body}</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f9f9;border:1px solid #e0e0e0;border-radius:8px;">
        <tr><td style="padding:20px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            {details}
          </table>
        </td></tr>
      </table>
      <p style="color:#888;font-size:12px;line-height:1.6;margin:24px 0 0;border-top:1px solid #eee;padding-top:16px;">This is a transactional email and cannot be unsubscribed from. &copy; 2026 EscrowShield. All rights reserved.</p>
    </td>
  </tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def detail_row(label, value, value_color='#1a1a2e'):
    return f"""<tr>
      <td style="padding:8px 16px 8px 0;vertical-align:top;width:50%;">
        <p style="color:#888;font-size:12px;margin:0 0 4px;text-transform:uppercase;letter-spacing:0.5px;">{label}</p>
        <p style="color:{value_color};font-size:15px;font-weight:500;margin:0;">{value}</p>
      </td>"""


def detail_pair(label1, value1, label2, value2, color1='#1a1a2e', color2='#1a1a2e'):
    return detail_row(label1, value1, color1) + detail_row(label2, value2, color2) + "</tr>"


class Command(BaseCommand):
    help = 'Seed all email templates with redesigned HTML'

    def handle(self, *args, **kwargs):
        templates = [
            # ── USER ──────────────────────────────────────────────
            {
                'event_type': 'terms_accepted',
                'subject': 'Welcome to EscrowShield',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Account Created',
                    'Welcome to EscrowShield!',
                    'Hi {{ user.first_name|default:user.username }}, your account has been successfully created. You have accepted our terms and conditions.',
                    detail_pair('Username', '{{ username }}', 'Email', '{{ email }}')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYour account has been created.\n\nUsername: {{ username }}\nEmail: {{ email }}',
            },
            {
                'event_type': 'account_verified',
                'subject': 'Your Account Has Been Verified',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Account Verified',
                    'Your account is verified!',
                    'Hi {{ user.first_name|default:user.username }}, your account has been verified by our team. You now have full access to all EscrowShield features.',
                    detail_pair('Username', '{{ user.username }}', 'Status', 'Verified', '#1a1a2e', '#0f6e56')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYour account has been verified.\n\nUsername: {{ user.username }}\nStatus: Verified',
            },

            # ── GIGS ──────────────────────────────────────────────
            {
                'event_type': 'gig_created',
                'subject': 'Your Gig Has Been Created - {{ title }}',
                'html_body': base_template(
                    '#e6f1fb', '#185fa5', 'Gig Created',
                    'Your gig has been posted!',
                    'Hi {{ user.first_name|default:user.username }}, your gig has been posted and is now visible to hustlers.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'Open', '#1a1a2e', '#185fa5')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYour gig "{{ title }}" has been posted.\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_accepted_client',
                'subject': 'Your Gig Has Been Accepted - {{ title }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Gig Accepted',
                    'Your gig has been accepted!',
                    'Hi {{ user.first_name|default:user.username }}, <strong>{{ hustler_name }}</strong> has accepted your gig and will begin work shortly.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Hustler', '{{ hustler_name }}')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\n{{ hustler_name }} has accepted your gig "{{ title }}".\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_accepted_hustler',
                'subject': 'You Have Accepted a Gig - {{ title }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Gig Accepted',
                    'You have accepted a gig!',
                    'Hi {{ user.first_name|default:user.username }}, you have accepted the gig <strong>{{ title }}</strong> and can begin work shortly.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'Accepted', '#1a1a2e', '#0f6e56')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYou have accepted the gig "{{ title }}".\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_started',
                'subject': 'Your Gig Is In Progress - {{ title }}',
                'html_body': base_template(
                    '#e6f1fb', '#185fa5', 'In Progress',
                    'Your gig is in progress!',
                    'Hi {{ user.first_name|default:user.username }}, <strong>{{ hustler_name }}</strong> has started working on your gig.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'In Progress', '#1a1a2e', '#185fa5')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\n{{ hustler_name }} has started working on your gig "{{ title }}".\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_pending_confirmation',
                'subject': 'Gig Awaiting Confirmation - {{ title }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Confirmation Required',
                    'Your gig is awaiting confirmation!',
                    'Hi {{ user.first_name|default:user.username }}, the gig <strong>{{ title }}</strong> has been marked complete and is awaiting your confirmation.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'Pending Confirmation', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYour gig "{{ title }}" is awaiting confirmation.\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_completed',
                'subject': 'Gig Completed - {{ title }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Completed',
                    'Gig completed successfully!',
                    'Hi {{ user.first_name|default:user.username }}, your gig <strong>{{ title }}</strong> has been completed successfully. Thank you for using EscrowShield!',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'Completed', '#1a1a2e', '#0f6e56')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYour gig "{{ title }}" has been completed.\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_cancelled',
                'subject': 'Gig Cancelled - {{ title }}',
                'html_body': base_template(
                    '#fcebeb', '#a32d2d', 'Cancelled',
                    'Your gig has been cancelled.',
                    'Hi {{ user.first_name|default:user.username }}, your gig <strong>{{ title }}</strong> has been cancelled. If you did not request this please contact support.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'Cancelled', '#1a1a2e', '#a32d2d')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nYour gig "{{ title }}" has been cancelled.\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },
            {
                'event_type': 'gig_disputed',
                'subject': 'Gig Disputed - {{ title }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Disputed',
                    'A dispute has been raised.',
                    'Hi {{ user.first_name|default:user.username }}, a dispute has been raised for your gig <strong>{{ title }}</strong>. Our team will review it shortly.',
                    detail_pair('Title', '{{ title }}', 'Budget', 'R{{ budget }}') +
                    detail_pair('Location', '{{ location }}', 'Status', 'Disputed', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nA dispute has been raised for your gig "{{ title }}".\n\nBudget: R{{ budget }}\nLocation: {{ location }}',
            },

            # ── TRANSACTIONS ──────────────────────────────────────
            {
                'event_type': 'transaction_draft',
                'subject': 'Transaction Created - {{ reference }}',
                'html_body': base_template(
                    '#e6f1fb', '#185fa5', 'Draft',
                    'Transaction created.',
                    'Hi {{ user.first_name|default:user.username }}, your transaction has been created and is currently in draft.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Draft', '#1a1a2e', '#185fa5')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nTransaction {{ reference }} created.\n\nAmount: R{{ amount }}\nType: {{ transaction_type }}',
            },
            {
                'event_type': 'awaiting_seller_acceptance',
                'subject': 'Awaiting Seller Acceptance - {{ reference }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Awaiting Acceptance',
                    'Waiting for seller to accept.',
                    'Hi {{ user.first_name|default:user.username }}, your transaction is awaiting the seller\'s acceptance.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Awaiting Acceptance', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nTransaction {{ reference }} awaiting seller acceptance.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'awaiting_payment',
                'subject': 'Payment Required - {{ reference }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Payment Required',
                    'Payment required.',
                    'Hi {{ user.first_name|default:user.username }}, the seller has accepted your transaction. Please proceed with your payment.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Awaiting Payment', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nPayment required for transaction {{ reference }}.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'payment_processing',
                'subject': 'Payment Processing - {{ reference }}',
                'html_body': base_template(
                    '#e6f1fb', '#185fa5', 'Processing',
                    'Your payment is being processed.',
                    'Hi {{ user.first_name|default:user.username }}, your payment is currently being processed. This usually takes a few minutes.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Processing', '#1a1a2e', '#185fa5')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nPayment processing for transaction {{ reference }}.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'transaction_funded',
                'subject': 'Transaction Funded - {{ reference }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Funded',
                    'Transaction funded!',
                    'Hi {{ user.first_name|default:user.username }}, your transaction has been funded and is held securely in escrow.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Funded', '#1a1a2e', '#0f6e56')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nTransaction {{ reference }} funded.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'in_delivery',
                'subject': 'Order In Delivery - {{ reference }}',
                'html_body': base_template(
                    '#e6f1fb', '#185fa5', 'In Delivery',
                    'Your order is on its way!',
                    'Hi {{ user.first_name|default:user.username }}, your order is on its way. Please confirm receipt once it arrives.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'In Delivery', '#1a1a2e', '#185fa5')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nOrder for transaction {{ reference }} is in delivery.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'buyer_confirmed',
                'subject': 'Delivery Confirmed - {{ reference }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Delivery Confirmed',
                    'Delivery confirmed!',
                    'Hi {{ user.first_name|default:user.username }}, you have confirmed receipt of your order. Funds of <strong>R{{ amount }}</strong> will now be released to the seller.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Status', 'Confirmed', 'Next Step', 'Funds Release', '#0f6e56', '#185fa5')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nDelivery confirmed for transaction {{ reference }}.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'funds_released',
                'subject': 'Funds Released - {{ reference }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Funds Released',
                    'Funds have been released!',
                    'Hi {{ user.first_name|default:user.username }}, the funds of <strong>R{{ amount }}</strong> for your transaction have been successfully released to the seller.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Status', 'Released', 'Type', '{{ transaction_type }}', '#0f6e56', '#1a1a2e')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nFunds of R{{ amount }} for transaction {{ reference }} released.',
            },
            {
                'event_type': 'transaction_cancelled',
                'subject': 'Transaction Cancelled - {{ reference }}',
                'html_body': base_template(
                    '#fcebeb', '#a32d2d', 'Cancelled',
                    'Transaction cancelled.',
                    'Hi {{ user.first_name|default:user.username }}, your transaction has been cancelled. If you did not request this please contact support.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Cancelled', '#1a1a2e', '#a32d2d')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nTransaction {{ reference }} cancelled.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'transaction_refunded',
                'subject': 'Transaction Refunded - {{ reference }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Refunded',
                    'Your transaction has been refunded.',
                    'Hi {{ user.first_name|default:user.username }}, your transaction has been resolved with a refund of <strong>R{{ amount }}</strong>.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Refunded', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nTransaction {{ reference }} refunded.\n\nAmount: R{{ amount }}',
            },
            {
                'event_type': 'transaction_completed',
                'subject': 'Transaction Complete - {{ reference }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Completed',
                    'Transaction completed!',
                    'Hi {{ user.first_name|default:user.username }}, your transaction has been completed successfully. Thank you for using EscrowShield.',
                    detail_pair('Reference', '{{ reference }}', 'Amount', 'R{{ amount }}') +
                    detail_pair('Type', '{{ transaction_type }}', 'Status', 'Completed', '#1a1a2e', '#0f6e56')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nTransaction {{ reference }} completed.\n\nAmount: R{{ amount }}',
            },

            # ── DISPUTES ──────────────────────────────────────────
            {
                'event_type': 'dispute_opened',
                'subject': 'Dispute Opened - {{ reference }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Dispute Opened',
                    'A dispute has been opened.',
                    'Hi {{ user.first_name|default:user.username }}, a dispute has been opened for your transaction. Our support team will review it shortly.',
                    detail_pair('Dispute ID', '{{ dispute_id }}', 'Transaction', '{{ reference }}') +
                    detail_pair('Reason', '{{ reason }}', 'Status', 'Open', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nDispute opened for transaction {{ reference }}.\n\nDispute ID: {{ dispute_id }}\nReason: {{ reason }}',
            },
            {
                'event_type': 'dispute_investigating',
                'subject': 'Dispute Under Investigation - {{ reference }}',
                'html_body': base_template(
                    '#faeeda', '#854f0b', 'Under Investigation',
                    'Your dispute is being investigated.',
                    'Hi {{ user.first_name|default:user.username }}, your dispute is currently being investigated by our support team. We will update you shortly.',
                    detail_pair('Dispute ID', '{{ dispute_id }}', 'Transaction', '{{ reference }}') +
                    detail_pair('Reason', '{{ reason }}', 'Status', 'Investigating', '#1a1a2e', '#854f0b')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nDispute {{ dispute_id }} is under investigation.\n\nTransaction: {{ reference }}\nReason: {{ reason }}',
            },
            {
                'event_type': 'dispute_resolved',
                'subject': 'Dispute Resolved - {{ reference }}',
                'html_body': base_template(
                    '#e1f5ee', '#0f6e56', 'Resolved',
                    'Your dispute has been resolved.',
                    'Hi {{ user.first_name|default:user.username }}, your dispute has been resolved by our support team.',
                    detail_pair('Dispute ID', '{{ dispute_id }}', 'Transaction', '{{ reference }}') +
                    detail_pair('Reason', '{{ reason }}', 'Status', '{{ status }}', '#1a1a2e', '#0f6e56')
                ),
                'plain_text_body': 'Hi {{ user.first_name|default:user.username }},\n\nDispute {{ dispute_id }} resolved.\n\nTransaction: {{ reference }}\nStatus: {{ status }}',
            },
        ]

        created, updated, skipped = 0, 0, 0
        for t in templates:
            obj, was_created = EmailTemplate.objects.get_or_create(
                event_type=t['event_type'],
                defaults={
                    'subject': t['subject'],
                    'html_body': t['html_body'],
                    'plain_text_body': t['plain_text_body'],
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
            else:
                obj.subject = t['subject']
                obj.html_body = t['html_body']
                obj.plain_text_body = t['plain_text_body']
                obj.is_active = True
                obj.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! {created} created, {updated} updated, {skipped} skipped.'
        ))