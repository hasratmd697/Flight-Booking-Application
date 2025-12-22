"""
Email Service Module
====================
Handles sending booking confirmation emails using SendGrid.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_ticket_email(ticket1, ticket2=None):
    """
    Send booking confirmation email to the user.
    
    Args:
        ticket1: Primary ticket object (required)
        ticket2: Return flight ticket object (optional, for round trips)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
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
        sendgrid_key = settings.SENDGRID_API_KEY if hasattr(settings, 'SENDGRID_API_KEY') else None
        
        if not sendgrid_key:
            print(f"[EMAIL] ERROR: SENDGRID_API_KEY not configured!")
            logger.error("SENDGRID_API_KEY is not configured")
            return False
        
        print(f"[EMAIL] Using SMTP with timeout=10s")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = recipient_email
        
        # Attach plain text and HTML
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to SendGrid with explicit timeout
        print(f"[EMAIL] Connecting to smtp.sendgrid.net:587...")
        server = smtplib.SMTP('smtp.sendgrid.net', 587, timeout=10)
        server.starttls()
        print(f"[EMAIL] TLS started, authenticating...")
        server.login('apikey', sendgrid_key)
        print(f"[EMAIL] Authenticated, sending message...")
        server.sendmail(settings.DEFAULT_FROM_EMAIL, [recipient_email], msg.as_string())
        server.quit()
        
        print(f"[EMAIL] SUCCESS: Email sent to {recipient_email}")
        logger.info(f"Booking confirmation email sent to {recipient_email} for ticket {ticket1.ref_no}")
        return True
        
    except smtplib.SMTPException as e:
        print(f"[EMAIL] SMTP ERROR: {str(e)}")
        logger.error(f"SMTP error sending email for ticket {ticket1.ref_no}: {str(e)}")
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
