from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from flight.models import *
import secrets
from datetime import datetime, timedelta

# PDF generation is optional - disabled for cloud deployment
try:
    from xhtml2pdf import pisa
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False
    pisa = None

from flight.constant import FEE

def render_to_pdf(template_src, context_dict={}):
    if not PDF_ENABLED:
        return HttpResponse("PDF generation is not available in this deployment.", status=503)
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def createticket(user,passengers,passengerscount,flight1,flight_1date,flight_1class,coupon,countrycode,email,mobile):
    ticket = Ticket.objects.create()
    ticket.user = user
    ticket.ref_no = secrets.token_hex(3).upper()
    for passenger in passengers:
        ticket.passengers.add(passenger)
    ticket.flight = flight1
    
    # Robust date parsing - handle multiple formats
    def parse_date(date_str):
        """Parse date string in either DD-MM-YYYY or YYYY-MM-DD format"""
        if not date_str:
            return datetime.now()
        
        date_str = str(date_str).strip()
        
        # Try DD-MM-YYYY format first (expected from form)
        if len(date_str.split('-')) == 3:
            parts = date_str.split('-')
            # Check if first part is 4 digits (YYYY-MM-DD format)
            if len(parts[0]) == 4:
                # YYYY-MM-DD format
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                # DD-MM-YYYY format
                return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        
        # Fallback to datetime parsing
        try:
            from dateutil import parser as date_parser
            return date_parser.parse(date_str)
        except:
            return datetime.now()
    
    flight_date = parse_date(flight_1date)
    ticket.flight_ddate = flight_date
    ###################
    flight1ddate = datetime(flight_date.year, flight_date.month, flight_date.day, flight1.depart_time.hour, flight1.depart_time.minute)
    flight1adate = (flight1ddate + flight1.duration)
    ###################
    ticket.flight_adate = datetime(flight1adate.year,flight1adate.month,flight1adate.day)
    ffre = 0.0
    if flight_1class.lower() == 'first':
        ticket.flight_fare = flight1.first_fare*int(passengerscount)
        ffre = flight1.first_fare*int(passengerscount)
    elif flight_1class.lower() == 'business':
        ticket.flight_fare = flight1.business_fare*int(passengerscount)
        ffre = flight1.business_fare*int(passengerscount)
    else:
        ticket.flight_fare = flight1.economy_fare*int(passengerscount)
        ffre = flight1.economy_fare*int(passengerscount)
    ticket.other_charges = FEE
    if coupon:
        ticket.coupon_used = coupon                     ##########Coupon
    ticket.total_fare = ffre+FEE+0.0                    ##########Total(Including coupon)
    ticket.seat_class = flight_1class.lower()
    ticket.status = 'PENDING'
    ticket.mobile = ('+'+countrycode+' '+mobile)
    ticket.email = email
    ticket.save()
    return ticket