"""
Email Service Module
====================
Handles sending booking confirmation emails using SendGrid Web API.
"""

from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_ticket_email(ticket1, ticket2=None):
    """
    Send booking confirmation email to the user using SendGrid Web API.
    
    Args:
        ticket1: Primary ticket object (required)
        ticket2: Return flight ticket object (optional, for round trips)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    import http.client
    import json
    
    try:
        # Get recipient email from ticket
        recipient_email = ticket1.email
        if not recipient_email:
            print(f"[EMAIL] No email address for ticket {ticket1.ref_no}")
            logger.warning(f"No email address for ticket {ticket1.ref_no}")
            return False
        
        print(f"[EMAIL] Building email for {recipient_email}")
        
        # Prepare context for email template
        context = {
            'ticket1': ticket1,
            'ticket2': ticket2,
            'is_round_trip': ticket2 is not None,
        }
        
        # Render HTML email from template
        html_content = render_to_string('flight/email_ticket.html', context)
        
        # Create plain text version by stripping HTML tags
        text_content = strip_tags(html_content)
        
        # Create email subject
        if ticket2:
            subject = f"Flight Booking Confirmed - {ticket1.flight.origin.code} to {ticket1.flight.destination.code} | Ref: {ticket1.ref_no}"
        else:
            subject = f"Flight Booking Confirmed - {ticket1.flight.origin.code} to {ticket1.flight.destination.code} | Ref: {ticket1.ref_no}"
        
        print(f"[EMAIL] Subject: {subject}")
        
        # Check if SendGrid is configured
        sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', None)
        
        if not sendgrid_key:
            print(f"[EMAIL] ERROR: SENDGRID_API_KEY not configured!")
            logger.error("SENDGRID_API_KEY is not configured")
            return False
        
        print(f"[EMAIL] Using SendGrid Web API (HTTPS)")
        
        # Prepare SendGrid API request
        from_email = settings.DEFAULT_FROM_EMAIL
        # Extract just the email address if it's in "Name <email>" format
        if '<' in from_email and '>' in from_email:
            from_name = from_email.split('<')[0].strip()
            from_addr = from_email.split('<')[1].replace('>', '').strip()
        else:
            from_name = "Flight Bookings"
            from_addr = from_email
        
        payload = {
            "personalizations": [
                {
                    "to": [{"email": recipient_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": from_addr,
                "name": from_name
            },
            "content": [
                {"type": "text/plain", "value": text_content},
                {"type": "text/html", "value": html_content}
            ]
        }
        
        # Send via SendGrid Web API
        print(f"[EMAIL] Sending via api.sendgrid.com...")
        
        conn = http.client.HTTPSConnection("api.sendgrid.com", timeout=15)
        headers = {
            "Authorization": f"Bearer {sendgrid_key}",
            "Content-Type": "application/json"
        }
        
        conn.request("POST", "/v3/mail/send", json.dumps(payload), headers)
        response = conn.getresponse()
        status = response.status
        body = response.read().decode('utf-8')
        conn.close()
        
        print(f"[EMAIL] SendGrid response: {status}")
        
        if status in (200, 201, 202):
            print(f"[EMAIL] SUCCESS: Email sent to {recipient_email}")
            logger.info(f"Booking confirmation email sent to {recipient_email} for ticket {ticket1.ref_no}")
            return True
        else:
            print(f"[EMAIL] FAILED: Status {status}, Body: {body}")
            logger.error(f"SendGrid API error for ticket {ticket1.ref_no}: {status} - {body}")
            return False
        
    except Exception as e:
        print(f"[EMAIL] ERROR: {str(e)}")
        import traceback
        print(f"[EMAIL] Traceback: {traceback.format_exc()}")
        logger.error(f"Failed to send email for ticket {ticket1.ref_no}: {str(e)}")
        return False


def resend_ticket_email(ticket_ref_no, user):
    """
    Resend ticket email for an existing booking.
    
    Args:
        ticket_ref_no: Ticket reference number
        user: User requesting the resend (for security check)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from .models import Ticket  # Import here to avoid circular imports
    
    try:
        # Find the ticket
        ticket1 = Ticket.objects.filter(ref_no=ticket_ref_no, user=user).first()
        
        if not ticket1:
            return False, "Ticket not found or access denied"
        
        # Check if there's a return ticket (same ref_no, different flight)
        ticket2 = Ticket.objects.filter(
            ref_no=ticket_ref_no, 
            user=user
        ).exclude(id=ticket1.id).first()
        
        # Send the email
        success = send_ticket_email(ticket1, ticket2)
        
        if success:
            return True, f"Email sent to {ticket1.email}"
        else:
            return False, "Failed to send email. Please try again."
            
    except Exception as e:
        logger.error(f"Error resending ticket email: {str(e)}")
        return False, "An error occurred. Please try again."
