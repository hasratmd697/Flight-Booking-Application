from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.utils import timezone

from datetime import datetime, timedelta
import math
import json
from .models import *
from capstone.utils import render_to_pdf, createticket


#Fee and Surcharge variable
from .constant import FEE
from flight.utils import createWeekDays, addPlaces, addDomesticFlights, addInternationalFlights
from flight.email_service import send_ticket_email
from flight.seat_manager import (
    get_seat_map, 
    reserve_seat, 
    book_seat, 
    release_seat,
    cleanup_expired_reservations,
    create_seats_for_flight
)
from flight.dynamic_pricing import get_dynamic_price, get_flight_prices_with_dynamic
from flight.flight_api import AmadeusFlightAPI, search_flights_api
import logging

logger = logging.getLogger(__name__)


class QuerySetLike(list):
    """
    A list subclass that mimics Django QuerySet behavior for templates.
    Allows template access like {{ flights.all.0.field }}
    """
    @property
    def all(self):
        return self
    
    def first(self):
        return self[0] if len(self) > 0 else None
    
    def last(self):
        return self[-1] if len(self) > 0 else None


class APIFlightWrapper:
    """
    Wrapper class that makes API flight offers compatible with existing templates.
    Mimics the Flight model interface expected by search.html template.
    """
    def __init__(self, api_offer, origin_place, destination_place):
        self.id = f"api_{api_offer.id}"  # Prefix to identify API results
        self.airline = api_offer.airline
        self.plane = api_offer.flight_number
        self.depart_time = api_offer.depart_time
        self.arrival_time = api_offer.arrival_time
        self.duration = api_offer.duration
        self.origin = origin_place
        self.destination = destination_place
        self.economy_fare = api_offer.economy_fare
        self.business_fare = api_offer.business_fare
        self.first_fare = api_offer.first_fare
        self.stops = api_offer.stops
        self._api_offer = api_offer  # Keep reference to original
    
    def __str__(self):
        return f"{self.origin.code} -> {self.destination.code} ({self.airline})"


def search_flights_with_api(origin, destination, departure_date, seat_class='economy'):
    """
    Search flights using API first, with database fallback.
    
    Args:
        origin: Place object for origin
        destination: Place object for destination
        departure_date: datetime object for departure date
        seat_class: 'economy', 'business', or 'first'
    
    Returns:
        tuple: (flights_list, is_from_api)
    """
    api = AmadeusFlightAPI()
    
    if api.is_available():
        try:
            date_str = departure_date.strftime('%Y-%m-%d')
            api_results = api.search_flights(
                origin.code, 
                destination.code, 
                date_str, 
                seat_class
            )
            
            if api_results:
                # Convert API results to template-compatible wrappers
                wrapped_flights = [
                    APIFlightWrapper(offer, origin, destination) 
                    for offer in api_results
                ]
                logger.info(f"API returned {len(wrapped_flights)} flights for {origin.code}->{destination.code}")
                return wrapped_flights, True
            else:
                logger.info(f"API returned no results for {origin.code}->{destination.code}, falling back to database")
        except Exception as e:
            logger.error(f"API search failed: {e}, falling back to database")
    
    return None, False


try:
    if len(Week.objects.all()) == 0:
        createWeekDays()

    if len(Place.objects.all()) == 0:
        addPlaces()
    
    # Flight seeding disabled - using Amadeus API for dynamic flight data
    # addDomesticFlights() and addInternationalFlights() are no longer used
except:
    pass

# Create your views here.

def index(request):
    # Use strftime for proper zero-padded date format (YYYY-MM-DD) required by HTML date inputs
    today = datetime.now().date()
    min_date = today.strftime("%Y-%m-%d")
    
    # Calculate max date (3 months from now)
    max_month = today.month + 3
    max_year = today.year
    if max_month > 12:
        max_month -= 12
        max_year += 1
    # Handle edge case where day might not exist in target month
    max_day = min(today.day, 28)  # Use 28 to be safe for all months
    max_date = f"{max_year}-{max_month:02d}-{max_day:02d}"
    if request.method == 'POST':
        origin = request.POST.get('Origin')
        destination = request.POST.get('Destination')
        depart_date = request.POST.get('DepartDate')
        seat = request.POST.get('SeatClass')
        trip_type = request.POST.get('TripType')
        if(trip_type == '1'):
            return render(request, 'flight/index.html', {
            'min_date': min_date,
            'max_date': max_date,
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date,
            'seat': seat.lower(),
            'trip_type': trip_type
        })
        elif(trip_type == '2'):
            return_date = request.POST.get('ReturnDate')
            return render(request, 'flight/index.html', {
            'min_date': min_date,
            'max_date': max_date,
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date,
            'seat': seat.lower(),
            'trip_type': trip_type,
            'return_date': return_date
        })
    else:
        return render(request, 'flight/index.html', {
            'min_date': min_date,
            'max_date': max_date
        })

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
            
        else:
            return render(request, "flight/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, "flight/login.html")

def register_view(request):
    if request.method == "POST":
        fname = request.POST['firstname']
        lname = request.POST['lastname']
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensuring password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "flight/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = fname
            user.last_name = lname
            user.save()
        except:
            return render(request, "flight/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "flight/register.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def query(request, q):
    import random
    places = list(Place.objects.all())
    q = q.lower().strip()
    
    # Handle random suggestions on focus
    if q == '_random':
        # Shuffle and return 8 random airports
        random.shuffle(places)
        sample = places[:8]
        return JsonResponse([{'code': p.code, 'city': p.city, 'country': p.country} for p in sample], safe=False)
    
    # Filter places based on search query
    filters = []
    for place in places:
        if (q in place.city.lower()) or (q in place.airport.lower()) or (q in place.code.lower()) or (q in place.country.lower()):
            filters.append(place)
    
    results = [{'code': place.code, 'city': place.city, 'country': place.country} for place in filters]
    
    # If query is exactly 3 letters and not already in results, suggest it as a custom code
    if len(q) == 3 and q.isalpha():
        q_upper = q.upper()
        if not any(r['code'] == q_upper for r in results):
            # Add the custom code as a suggestion
            results.insert(0, {'code': q_upper, 'city': f'{q_upper} (Any IATA Code)', 'country': 'Use this code directly'})
    
    return JsonResponse(results, safe=False)

@csrf_exempt
def flight(request):
    o_place = request.GET.get('Origin')
    d_place = request.GET.get('Destination')
    trip_type = request.GET.get('TripType')
    departdate = request.GET.get('DepartDate')
    depart_date = datetime.strptime(departdate, "%Y-%m-%d")
    return_date = None
    seat = request.GET.get('SeatClass')
    
    # Validate origin and destination codes - accept any valid 3-letter IATA code
    o_code = o_place.upper().strip()
    d_code = d_place.upper().strip()
    
    # Validate IATA codes (3 letters)
    if len(o_code) != 3 or not o_code.isalpha():
        return render(request, 'flight/error.html', {
            'error_title': 'Invalid Origin Airport',
            'error_message': f"'{o_code}' is not a valid airport code. Please enter a 3-letter IATA code (e.g., JFK, LAX, LHR).",
            'show_search': True
        })
    
    if len(d_code) != 3 or not d_code.isalpha():
        return render(request, 'flight/error.html', {
            'error_title': 'Invalid Destination Airport',
            'error_message': f"'{d_code}' is not a valid airport code. Please enter a 3-letter IATA code (e.g., JFK, LAX, LHR).",
            'show_search': True
        })
    
    # Get or create Place objects for any valid IATA code
    origin, _ = Place.objects.get_or_create(
        code=o_code,
        defaults={
            'city': o_code,  # Use code as city name if unknown
            'airport': f'{o_code} Airport',
            'country': 'Unknown'
        }
    )
    
    destination, _ = Place.objects.get_or_create(
        code=d_code,
        defaults={
            'city': d_code,
            'airport': f'{d_code} Airport',
            'country': 'Unknown'
        }
    )
    
    if trip_type == '2':
        returndate = request.GET.get('ReturnDate')
        return_date = datetime.strptime(returndate, "%Y-%m-%d")
        origin2 = destination   ##
        destination2 = origin  ##

    # Initialize variables
    flights = []
    flights2 = []
    max_price = 0
    min_price = 0
    max_price2 = 0
    min_price2 = 0
    
    # API-only mode - fetch flights from Amadeus API
    api_flights, from_api = search_flights_with_api(origin, destination, depart_date, seat)
    
    if api_flights:
        # Use API results
        flights = api_flights
        # Sort by fare based on seat class and wrap in QuerySetLike for template compatibility
        if seat == 'economy':
            flights = QuerySetLike(sorted(flights, key=lambda f: f.economy_fare))
            fares = [f.economy_fare for f in flights]
        elif seat == 'business':
            flights = QuerySetLike(sorted(flights, key=lambda f: f.business_fare))
            fares = [f.business_fare for f in flights]
        else:  # first
            flights = QuerySetLike(sorted(flights, key=lambda f: f.first_fare))
            fares = [f.first_fare for f in flights]
        
        if fares:
            min_price = min(fares)
            max_price = max(fares)
        
        # Handle return flight for round trip
        if trip_type == '2':
            api_flights2, _ = search_flights_with_api(origin2, destination2, return_date, seat)
            if api_flights2:
                # Append suffix to return flight IDs to prevent collision with outbound flights
                for f in api_flights2:
                    f.id = f"{f.id}_return"
                    
                flights2 = api_flights2
                if seat == 'economy':
                    flights2 = QuerySetLike(sorted(flights2, key=lambda f: f.economy_fare))
                    fares2 = [f.economy_fare for f in flights2]
                elif seat == 'business':
                    flights2 = QuerySetLike(sorted(flights2, key=lambda f: f.business_fare))
                    fares2 = [f.business_fare for f in flights2]
                else:
                    flights2 = QuerySetLike(sorted(flights2, key=lambda f: f.first_fare))
                    fares2 = [f.first_fare for f in flights2]
                
                if fares2:
                    min_price2 = min(fares2)
                    max_price2 = max(fares2)

    # Store API flights in session for later retrieval when booking
    api_flights_data = {}
    for f in flights:
        if hasattr(f, '_api_offer'):
            api_flights_data[f.id] = {
                'airline': f.airline,
                'plane': f.plane,
                'depart_time': f.depart_time.isoformat() if hasattr(f.depart_time, 'isoformat') else str(f.depart_time),
                'arrival_time': f.arrival_time.isoformat() if hasattr(f.arrival_time, 'isoformat') else str(f.arrival_time),
                'duration_seconds': int(f.duration.total_seconds()),
                'origin_code': f.origin.code,
                'destination_code': f.destination.code,
                'economy_fare': float(f.economy_fare),
                'business_fare': float(f.business_fare),
                'first_fare': float(f.first_fare),
            }
    # Also store return flights if round trip
    if trip_type == '2' and flights2:
        for f in flights2:
            if hasattr(f, '_api_offer'):
                api_flights_data[f.id] = {
                    'airline': f.airline,
                    'plane': f.plane,
                    'depart_time': f.depart_time.isoformat() if hasattr(f.depart_time, 'isoformat') else str(f.depart_time),
                    'arrival_time': f.arrival_time.isoformat() if hasattr(f.arrival_time, 'isoformat') else str(f.arrival_time),
                    'duration_seconds': int(f.duration.total_seconds()),
                    'origin_code': f.origin.code,
                    'destination_code': f.destination.code,
                    'economy_fare': float(f.economy_fare),
                    'business_fare': float(f.business_fare),
                    'first_fare': float(f.first_fare),
                }
    request.session['api_flights'] = api_flights_data

    if trip_type == '2':
        return render(request, "flight/search.html", {
            'flights': flights,
            'origin': origin,
            'destination': destination,
            'flights2': flights2,   ##
            'origin2': origin2,    ##
            'destination2': destination2,    ##
            'seat': seat.capitalize(),
            'trip_type': trip_type,
            'depart_date': depart_date,
            'return_date': return_date,
            'max_price': math.ceil(max_price/100)*100,
            'min_price': math.floor(min_price/100)*100,
            'max_price2': math.ceil(max_price2/100)*100,    ##
            'min_price2': math.floor(min_price2/100)*100    ##
        })
    else:
        return render(request, "flight/search.html", {
            'flights': flights,
            'origin': origin,
            'destination': destination,
            'seat': seat.capitalize(),
            'trip_type': trip_type,
            'depart_date': depart_date,
            'return_date': return_date,
            'max_price': math.ceil(max_price/100)*100,
            'min_price': math.floor(min_price/100)*100
        })

def review(request):
    flight_1 = request.GET.get('flight1Id')
    date1 = request.GET.get('flight1Date')
    seat = request.GET.get('seatClass')
    selected_seats = request.GET.get('selectedSeats', '')  # Comma-separated seat IDs
    round_trip = False
    if request.GET.get('flight2Id'):
        round_trip = True

    if round_trip:
        flight_2 = request.GET.get('flight2Id')
        date2 = request.GET.get('flight2Date')

    # Helper function to parse multiple date formats
    def parse_date_flexible(date_str):
        """Parse date string trying multiple formats"""
        if not date_str:
            return None
        
        formats = [
            '%d-%m-%Y',              # 12-12-2025
            '%Y-%m-%d',              # 2025-12-12
            '%b. %d, %Y, midnight',  # Dec. 13, 2025, midnight
            '%b. %d, %Y, noon',      # Dec. 13, 2025, noon
            '%b. %d, %Y',            # Dec. 13, 2025
            '%B %d, %Y',             # December 13, 2025
            '%d %b %Y',              # 13 Dec 2025
        ]
        
        date_str = date_str.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Handle "Dec. 13, 2025, midnight" format specifically
        try:
            cleaned = date_str.replace(', midnight', '').replace(', noon', '')
            return datetime.strptime(cleaned, '%b. %d, %Y')
        except:
            pass
        
        return None

    if request.user.is_authenticated:
        flight1 = Flight.objects.get(id=flight_1)
        
        # Parse date using flexible parser
        parsed_date1 = parse_date_flexible(date1)
        if parsed_date1:
            flight1ddate = datetime(parsed_date1.year, parsed_date1.month, parsed_date1.day, 
                                   flight1.depart_time.hour, flight1.depart_time.minute)
        else:
            # Fallback to current date if parsing fails
            flight1ddate = datetime.now().replace(hour=flight1.depart_time.hour, 
                                                   minute=flight1.depart_time.minute)
        
        flight1adate = (flight1ddate + flight1.duration)
        flight2 = None
        flight2ddate = None
        flight2adate = None
        if round_trip:
            flight2 = Flight.objects.get(id=flight_2)
            parsed_date2 = parse_date_flexible(date2)
            if parsed_date2:
                flight2ddate = datetime(parsed_date2.year, parsed_date2.month, parsed_date2.day,
                                       flight2.depart_time.hour, flight2.depart_time.minute)
            else:
                flight2ddate = datetime.now().replace(hour=flight2.depart_time.hour,
                                                       minute=flight2.depart_time.minute)
            flight2adate = (flight2ddate + flight2.duration)
        
        # Get selected seat objects if any
        seat_objects = []
        required_passengers = 1  # Default to at least 1 passenger
        if selected_seats:
            seat_ids = [int(sid) for sid in selected_seats.split(',') if sid.strip()]
            seat_objects = Seat.objects.filter(id__in=seat_ids)
            # Calculate required passengers from selected seats
            # For round trips, seats are selected for both flights, so divide by 2
            if round_trip:
                required_passengers = max(1, len(seat_ids) // 2)
            else:
                required_passengers = max(1, len(seat_ids))
        
        if round_trip:
            return render(request, "flight/book.html", {
                'flight1': flight1,
                'flight2': flight2,
                "flight1ddate": flight1ddate,
                "flight1adate": flight1adate,
                "flight2ddate": flight2ddate,
                "flight2adate": flight2adate,
                "seat": seat,
                "fee": FEE,
                "selected_seats": seat_objects,
                "required_passengers": required_passengers
            })
        return render(request, "flight/book.html", {
            'flight1': flight1,
            "flight1ddate": flight1ddate,
            "flight1adate": flight1adate,
            "seat": seat,
            "fee": FEE,
            "selected_seats": seat_objects,
            "required_passengers": required_passengers
        })
    else:
        return HttpResponseRedirect(reverse("login"))

def select_flight(request):
    """
    Intermediate view for flight selection
    Creates database Flight entries from API flight data for seat selection
    """
    flight_1 = request.GET.get('flight1Id')
    date1 = request.GET.get('flight1Date')
    seat = request.GET.get('seatClass', 'economy').lower()
    
    # Round trip parameters
    flight_2 = request.GET.get('flight2Id')
    date2 = request.GET.get('flight2Date')
    is_round_trip = flight_2 is not None and flight_2 != ''
    
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    # Helper function to get or create flight from API data
    def get_or_create_api_flight(flight_id):
        api_flights = request.session.get('api_flights', {})
        flight_data = api_flights.get(flight_id)
        
        if not flight_data:
            return None, "Flight data expired"
        
        try:
            origin = Place.objects.get(code=flight_data['origin_code'])
            destination = Place.objects.get(code=flight_data['destination_code'])
            
            from dateutil import parser as date_parser
            depart_time = date_parser.parse(flight_data['depart_time']).time()
            arrival_time = date_parser.parse(flight_data['arrival_time']).time()
            duration = timedelta(seconds=flight_data['duration_seconds'])
            
            flight, created = Flight.objects.get_or_create(
                plane=flight_data['plane'],
                origin=origin,
                destination=destination,
                depart_time=depart_time,
                defaults={
                    'airline': flight_data['airline'],
                    'arrival_time': arrival_time,
                    'duration': duration,
                    'economy_fare': flight_data['economy_fare'],
                    'business_fare': flight_data['business_fare'],
                    'first_fare': flight_data['first_fare'],
                }
            )
            
            if created:
                for day in Week.objects.all():
                    flight.depart_day.add(day)
                flight.save()
                logger.info(f"Created new Flight record from API: {flight.plane}")
            
            return flight, None
        except Exception as e:
            logger.error(f"Error creating flight from API data: {e}")
            return None, str(e)
    
    # Process first flight
    db_flight1_id = flight_1
    if str(flight_1).startswith('api_'):
        flight_obj, error = get_or_create_api_flight(flight_1)
        if error:
            return render(request, 'flight/error.html', {
                'error_title': 'Flight Not Found',
                'error_message': f'The selected flight data has expired. Please search again. ({error})',
                'show_search': True
            })
        db_flight1_id = flight_obj.id
    
    # Build redirect URL
    redirect_url = f"/flight/seats?flight_id={db_flight1_id}&seat_class={seat}&depart_date={date1}"
    
    # Process second flight for round trips
    if is_round_trip:
        db_flight2_id = flight_2
        if str(flight_2).startswith('api_'):
            flight2_obj, error = get_or_create_api_flight(flight_2)
            if error:
                return render(request, 'flight/error.html', {
                    'error_title': 'Return Flight Not Found',
                    'error_message': f'The return flight data has expired. Please search again. ({error})',
                    'show_search': True
                })
            db_flight2_id = flight2_obj.id
        
        redirect_url += f"&flight2_id={db_flight2_id}&date2={date2}&round_trip=true"
    
    return HttpResponseRedirect(redirect_url)

def book(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            flight_1 = request.POST.get('flight1')
            flight_1date = request.POST.get('flight1Date')
            flight_1class = request.POST.get('flight1Class')
            f2 = False
            if request.POST.get('flight2'):
                flight_2 = request.POST.get('flight2')
                flight_2date = request.POST.get('flight2Date')
                flight_2class = request.POST.get('flight2Class')
                f2 = True
            countrycode = request.POST['countryCode']
            mobile = request.POST['mobile']
            email = request.POST['email']
            flight1 = Flight.objects.get(id=flight_1)
            if f2:
                flight2 = Flight.objects.get(id=flight_2)
            passengerscount = request.POST['passengersCount']
            
            # Server-side validation: Check passenger count matches seat selection
            selected_seat_ids = request.POST.getlist('selected_seats')
            if selected_seat_ids:
                # For round trips, seats are selected for both flights
                if f2:
                    required_passengers = max(1, len(selected_seat_ids) // 2)
                else:
                    required_passengers = len(selected_seat_ids)
                
                passenger_count = int(passengerscount) if passengerscount else 0
                
                if passenger_count != required_passengers:
                    # Return error with proper context for re-rendering book page
                    return render(request, 'flight/error.html', {
                        'error_title': 'Passenger Count Mismatch',
                        'error_message': f'You selected {required_passengers} seat(s) but provided details for {passenger_count} passenger(s). '
                                        f'Please go back and ensure the number of passengers matches your seat selection.',
                        'show_back': True
                    })
            passengers=[]
            for i in range(1,int(passengerscount)+1):
                fname = request.POST[f'passenger{i}FName']
                lname = request.POST[f'passenger{i}LName']
                gender = request.POST[f'passenger{i}Gender']
                passengers.append(Passenger.objects.create(first_name=fname,last_name=lname,gender=gender.lower()))
            coupon = request.POST.get('coupon')
            coupon_discount = int(request.POST.get('couponDiscount', 0) or 0)
            
            try:
                ticket1 = createticket(request.user,passengers,passengerscount,flight1,flight_1date,flight_1class,coupon,countrycode,email,mobile)
                if f2:
                    ticket2 = createticket(request.user,passengers,passengerscount,flight2,flight_2date,flight_2class,coupon,countrycode,email,mobile)

                if(flight_1class == 'Economy'):
                    if f2:
                        fare = (flight1.economy_fare*int(passengerscount))+(flight2.economy_fare*int(passengerscount))
                    else:
                        fare = flight1.economy_fare*int(passengerscount)
                elif (flight_1class == 'Business'):
                    if f2:
                        fare = (flight1.business_fare*int(passengerscount))+(flight2.business_fare*int(passengerscount))
                    else:
                        fare = flight1.business_fare*int(passengerscount)
                elif (flight_1class == 'First'):
                    if f2:
                        fare = (flight1.first_fare*int(passengerscount))+(flight2.first_fare*int(passengerscount))
                    else:
                        fare = flight1.first_fare*int(passengerscount)
            except Exception as e:
                return HttpResponse(e)
            
            # Link Selected Seats to Tickets
            selected_seat_ids = request.POST.getlist('selected_seats')
            if selected_seat_ids:
                seats = Seat.objects.filter(id__in=selected_seat_ids)
                for seat in seats:
                    # Update reservation to prevent expiry during payment
                    reserve_seat(seat.id)
                    
                    if seat.flight == flight1:
                        ticket1.selected_seats.add(seat)
                    elif f2 and flight2 and seat.flight == flight2:
                        ticket2.selected_seats.add(seat)
            

            if f2:    ##
                final_fare = max(0, fare + FEE - coupon_discount)
                return render(request, "flight/payment.html", { ##
                    'fare': final_fare,   ##
                    'ticket': ticket1.id,   ##
                    'ticket2': ticket2.id   ##
                })  ##
            final_fare = max(0, fare + FEE - coupon_discount)
            return render(request, "flight/payment.html", {
                'fare': final_fare,
                'ticket': ticket1.id
            })
        else:
            return HttpResponseRedirect(reverse("login"))
    else:
        return HttpResponse("Method must be post.")

def payment(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # Import payment simulator
            from payment_simulate import process_payment
            
            ticket_id = request.POST['ticket']
            t2 = False
            if request.POST.get('ticket2'):
                ticket2_id = request.POST['ticket2']
                t2 = True
            fare = float(request.POST.get('fare', 0))
            card_number = request.POST['cardNumber'].replace(' ', '')
            card_holder_name = request.POST['cardHolderName']
            exp_month = request.POST['expMonth']
            exp_year = request.POST['expYear']
            cvv = request.POST['cvv']
            
            # Format expiry as MM/YY for payment simulator
            try:
                exp_year_short = str(int(exp_year))[-2:]  # Get last 2 digits
                expiry = f"{exp_month.zfill(2)}/{exp_year_short}"
            except:
                expiry = ""
            
            # Validate card holder name
            import re
            validation_errors = []
            if not re.match(r'^[a-zA-Z\s]+$', card_holder_name) or len(card_holder_name) < 2:
                validation_errors.append("Invalid card holder name. Letters only.")
                print(f"[PAYMENT] Validation failed: Invalid card holder name")
            
            if validation_errors:
                ticket = Ticket.objects.get(id=ticket_id)
                return render(request, 'flight/payment.html', {
                    'fare': ticket.total_fare,
                    'ticket': ticket_id,
                    'ticket2': ticket2_id if t2 else None,
                    'errors': validation_errors
                })
            
            # Process payment through simulator
            print(f"[PAYMENT] Processing card payment for ₹{fare}...")
            result = process_payment(
                payment_method='card',
                amount=fare,
                card_number=card_number,
                expiry=expiry,
                cvv=cvv
            )
            
            print(f"[PAYMENT] Gateway response: {result}")
            
            # Handle payment failure
            if not result.get('success'):
                print(f"[PAYMENT] Payment FAILED: {result.get('errors', ['Unknown error'])}")
                ticket = Ticket.objects.get(id=ticket_id)
                return render(request, 'flight/payment.html', {
                    'fare': ticket.total_fare,
                    'ticket': ticket_id,
                    'ticket2': ticket2_id if t2 else None,
                    'errors': result.get('errors', ['Payment processing failed. Please try again.']),
                    'transaction_id': result.get('transaction_id')
                })
            
            # Payment successful - confirm booking
            transaction_id = result.get('transaction_id')
            print(f"[PAYMENT] Payment SUCCESS! Transaction ID: {transaction_id}")

            try:
                ticket = Ticket.objects.get(id=ticket_id)
                ticket.status = 'CONFIRMED'
                ticket.booking_date = datetime.now()
                ticket.save()
                
                # Book seats for ticket 1
                for seat in ticket.selected_seats.all():
                    book_seat(seat.id)
                    
                print(f"[PAYMENT] Ticket {ticket.ref_no} CONFIRMED!")
                
                if t2:
                    ticket2 = Ticket.objects.get(id=ticket2_id)
                    ticket2.status = 'CONFIRMED'
                    ticket2.save()
                    
                    # Book seats for ticket 2
                    for seat in ticket2.selected_seats.all():
                        book_seat(seat.id)
                        
                    print(f"[PAYMENT] Round-trip ticket {ticket2.ref_no} CONFIRMED!")
                    
                    # Send confirmation email in background (non-blocking to prevent timeout)
                    import threading
                    def send_email_async():
                        try:
                            send_ticket_email(ticket, ticket2)
                            print(f"[EMAIL] Confirmation email sent successfully")
                        except Exception as e:
                            print(f"[EMAIL] Failed to send email: {e}")
                    
                    email_thread = threading.Thread(target=send_email_async)
                    email_thread.start()
                    
                    return render(request, 'flight/payment_process.html', {
                        'ticket1': ticket,
                        'ticket2': ticket2,
                        'transaction_id': transaction_id,
                        'email_sent': True,  # Assume success, email sends in background
                        'email_address': ticket.email
                    })
                
                # Send confirmation email in background (non-blocking) for one-way trip
                import threading
                def send_email_async():
                    try:
                        send_ticket_email(ticket)
                        print(f"[EMAIL] Confirmation email sent successfully")
                    except Exception as e:
                        print(f"[EMAIL] Failed to send email: {e}")
                
                email_thread = threading.Thread(target=send_email_async)
                email_thread.start()
                
                return render(request, 'flight/payment_process.html', {
                    'ticket1': ticket,
                    'ticket2': "",
                    'transaction_id': transaction_id,
                    'email_sent': True,  # Assume success, email sends in background
                    'email_address': ticket.email
                })
            except Exception as e:
                print(f"[PAYMENT] ERROR: {str(e)}")
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be post.")
    else:
        return HttpResponseRedirect(reverse('login'))


def ticket_data(request, ref):
    ticket = Ticket.objects.get(ref_no=ref)
    return JsonResponse({
        'ref': ticket.ref_no,
        'from': ticket.flight.origin.code,
        'to': ticket.flight.destination.code,
        'flight_date': ticket.flight_ddate,
        'status': ticket.status
    })

@csrf_exempt
def get_ticket(request):
    ref = request.GET.get("ref")
    ticket1 = Ticket.objects.get(ref_no=ref)
    data = {
        'ticket1':ticket1,
        'current_year': datetime.now().year
    }
    pdf = render_to_pdf('flight/ticket.html', data)
    return HttpResponse(pdf, content_type='application/pdf')


def bookings(request):
    if request.user.is_authenticated:
        tickets = Ticket.objects.filter(user=request.user).order_by('-booking_date')
        return render(request, 'flight/bookings.html', {
            'page': 'bookings',
            'tickets': tickets
        })
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def resend_ticket_email_view(request):
    """
    Resend booking confirmation email to user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login first'})
    
    if request.method == 'POST':
        ref_no = request.POST.get('ref_no')
        if not ref_no:
            return JsonResponse({'success': False, 'message': 'Missing ticket reference'})
        
        # Find ticket and resend email
        try:
            ticket1 = Ticket.objects.filter(ref_no=ref_no, user=request.user).first()
            if not ticket1:
                return JsonResponse({'success': False, 'message': 'Ticket not found'})
            
            # Check for return ticket
            ticket2 = Ticket.objects.filter(ref_no=ref_no, user=request.user).exclude(id=ticket1.id).first()
            
            # Send email
            success = send_ticket_email(ticket1, ticket2)
            
            if success:
                return JsonResponse({'success': True, 'message': f'Email sent to {ticket1.email}'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send email. Please try again.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def cancel_ticket(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            ref = request.POST['ref']
            try:
                ticket = Ticket.objects.get(ref_no=ref)
                if ticket.user == request.user:
                    ticket.status = 'CANCELLED'
                    ticket.save()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({
                        'success': False,
                        'error': "User unauthorised"
                    })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': e
                })
        else:
            return HttpResponse("User unauthorised")
    else:
        return HttpResponse("Method must be POST.")

def resume_booking(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            ref = request.POST['ref']
            ticket = Ticket.objects.get(ref_no=ref)
            if ticket.user == request.user:
                return render(request, "flight/payment.html", {
                    'fare': ticket.total_fare,
                    'ticket': ticket.id
                })
            else:
                return HttpResponse("User unauthorised")
        else:
            return HttpResponseRedirect(reverse("login"))
    else:
        return HttpResponse("Method must be post.")

def contact(request):
    return render(request, 'flight/contact.html')

def privacy_policy(request):
    return render(request, 'flight/privacy-policy.html')

def terms_and_conditions(request):
    return render(request, 'flight/terms.html')

def about_us(request):
    return render(request, 'flight/about.html')


@csrf_exempt
def seat_selection(request):
    """
    Display seat selection page for a flight
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    
    flight_id = request.GET.get('flight_id')
    seat_class = request.GET.get('seat_class', 'economy')
    depart_date = request.GET.get('depart_date')
    
    # Round trip parameters
    flight2_id = request.GET.get('flight2_id')
    date2 = request.GET.get('date2')
    round_trip = request.GET.get('round_trip') == 'true'
    
    try:
        flight = Flight.objects.get(id=flight_id)
        
        # Check if seats exist for this flight, if not create them
        if not flight.seats.exists():
            create_seats_for_flight(flight)
        
        # Clean up expired reservations
        cleanup_expired_reservations()
        
        # Get seat map
        seats = Seat.objects.filter(
            flight=flight,
            seat_class=seat_class
        ).order_by('seat_number')
        
        # Organize seats into rows
        seat_layout = {}
        for seat in seats:
            row = ''.join(filter(str.isdigit, seat.seat_number))
            col = ''.join(filter(str.isalpha, seat.seat_number))
            
            if row not in seat_layout:
                seat_layout[row] = {}
            
            seat_layout[row][col] = {
                'id': seat.id,
                'number': seat.seat_number,
                'status': seat.status,
                'price': seat.price
            }
        
        # Parse depart_date for proper formatting (handle multiple date formats)
        from datetime import datetime, timedelta
        
        def parse_date(date_str):
            """Parse date string trying multiple formats"""
            if not date_str:
                return None
            
            # List of date formats to try
            formats = [
                '%d-%m-%Y',              # 12-12-2025
                '%Y-%m-%d',              # 2025-12-12
                '%b. %d, %Y, %H:%M',     # Dec. 12, 2025, 00:00
                '%b. %d, %Y, midnight',  # Dec. 12, 2025, midnight
                '%b. %d, %Y, noon',      # Dec. 12, 2025, noon
                '%b. %d, %Y',            # Dec. 12, 2025
                '%B %d, %Y',             # December 12, 2025
                '%d %b %Y',              # 12 Dec 2025
                '%d %B %Y',              # 12 December 2025
            ]
            
            # Clean the date string
            date_str = date_str.strip()
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If none of the formats work, try a more flexible approach
            # Handle "Dec. 12, 2025, midnight" format specifically
            try:
                # Remove ", midnight" or ", noon" suffix
                cleaned = date_str.replace(', midnight', '').replace(', noon', '')
                return datetime.strptime(cleaned, '%b. %d, %Y')
            except:
                pass
            
            return None
        
        try:
            depart_date_obj = parse_date(depart_date)
            if depart_date_obj:
                arrival_date_obj = depart_date_obj + timedelta(seconds=flight.duration.total_seconds())
            else:
                arrival_date_obj = None
        except:
            depart_date_obj = None
            arrival_date_obj = None
        
        # Prepare context
        context = {
            'flight': flight,
            'seat_class': seat_class,
            'seat_layout': seat_layout,
            'depart_date': depart_date_obj,
            'arrival_date': arrival_date_obj,
            'flight_id': flight_id,
            'round_trip': round_trip,
        }
        
        # Add round trip data if applicable
        if round_trip and flight2_id:
            try:
                flight2 = Flight.objects.get(id=flight2_id)
                
                # Check if seats exist for return flight
                if not flight2.seats.exists():
                    create_seats_for_flight(flight2)
                
                # Parse date2 for proper formatting (using same multi-format parser)
                try:
                    date2_obj = parse_date(date2)
                    if date2_obj:
                        arrival_date2_obj = date2_obj + timedelta(seconds=flight2.duration.total_seconds())
                    else:
                        arrival_date2_obj = None
                except:
                    date2_obj = None
                    arrival_date2_obj = None
                
                context['flight2'] = flight2
                context['flight2_id'] = flight2_id
                context['date2'] = date2_obj
                context['arrival_date2'] = arrival_date2_obj
            except Flight.DoesNotExist:
                context['flight2_error'] = 'Return flight not found'
        
        return render(request, 'flight/seat_selection.html', context)
    except Flight.DoesNotExist:
        return HttpResponse("Flight not found", status=404)


@csrf_exempt
def get_available_seats(request):
    """
    Get available seats for a flight (AJAX endpoint)
    Now includes DYNAMIC PRICING based on seat occupancy!
    """
    if request.method == 'GET':
        flight_id = request.GET.get('flight_id')
        seat_class = request.GET.get('seat_class', 'economy')
        
        try:
            flight = Flight.objects.get(id=flight_id)
            
            # Clean up expired reservations first
            cleanup_expired_reservations()
            
            seats = Seat.objects.filter(
                flight=flight,
                seat_class=seat_class
            ).order_by('seat_number')
            
            # ===== DYNAMIC PRICING CALCULATION =====
            # Calculate current occupancy for this flight
            total_seats = seats.count()
            occupied_seats = seats.filter(status__in=['booked', 'reserved']).count()
            
            if total_seats > 0:
                occupancy_rate = occupied_seats / total_seats
            else:
                occupancy_rate = 0.0
            
            # Import and use dynamic pricing multiplier
            from flight.dynamic_pricing import get_occupancy_multiplier
            price_multiplier = get_occupancy_multiplier(occupancy_rate)
            
            # Log the dynamic pricing calculation
            logger.info(f"[DYNAMIC PRICING API] Flight {flight_id}: {occupied_seats}/{total_seats} seats occupied ({occupancy_rate:.1%})")
            logger.info(f"[DYNAMIC PRICING API] Price multiplier: {price_multiplier}x")
            # ========================================
            
            seat_data = []
            for seat in seats:
                # Apply dynamic pricing multiplier to base price
                base_price = seat.price
                dynamic_price = round(base_price * price_multiplier, 2)
                
                seat_data.append({
                    'id': seat.id,
                    'number': seat.seat_number,
                    'status': seat.status,
                    'price': dynamic_price,  # Now returns DYNAMIC price!
                    'base_price': base_price,  # Also include base price for reference
                    'reserved_until': seat.reserved_until.isoformat() if seat.reserved_until else None
                })
            
            return JsonResponse({
                'success': True, 
                'seats': seat_data,
                'pricing_info': {
                    'occupancy_rate': round(occupancy_rate * 100, 1),
                    'price_multiplier': price_multiplier,
                    'total_seats': total_seats,
                    'occupied_seats': occupied_seats
                }
            })
        except Flight.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Flight not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@transaction.atomic
def reserve_seat_view(request):
    """
    Reserve a seat temporarily (AJAX endpoint)
    Uses database transactions and row-level locking for concurrency control
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            seat_id = data.get('seat_id')
            
            if not seat_id:
                return JsonResponse({'success': False, 'error': 'Seat ID is required'})
            
            result = reserve_seat(seat_id, duration_minutes=10)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@transaction.atomic
def release_seat_view(request):
    """
    Release a reserved seat (AJAX endpoint)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            seat_id = data.get('seat_id')
            
            if not seat_id:
                return JsonResponse({'success': False, 'error': 'Seat ID is required'})
            
            result = release_seat(seat_id)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@transaction.atomic
def confirm_seat_booking(request):
    """
    Confirm seat booking and link to ticket
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            seat_ids = data.get('seat_ids', [])
            ticket_id = data.get('ticket_id')
            
            if not seat_ids:
                return JsonResponse({'success': False, 'error': 'No seats selected'})
            
            # Book all selected seats
            booked_seats = []
            for seat_id in seat_ids:
                result = book_seat(seat_id)
                if result['success']:
                    booked_seats.append(seat_id)
                else:
                    # Rollback - release already booked seats
                    for booked_id in booked_seats:
                        release_seat(booked_id)
                    return JsonResponse({
                        'success': False, 
                        'error': f"Failed to book seat: {result.get('error')}"
                    })
            
            # Link seats to ticket if provided
            if ticket_id:
                try:
                    ticket = Ticket.objects.get(id=ticket_id)
                    for seat_id in booked_seats:
                        seat = Seat.objects.get(id=seat_id)
                        ticket.selected_seats.add(seat)
                    ticket.save()
                except Ticket.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Ticket not found'})
            
            return JsonResponse({
                'success': True, 
                'message': f'{len(booked_seats)} seat(s) booked successfully',
                'booked_seats': booked_seats
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Dynamic Pricing API
@csrf_exempt
def get_dynamic_price_api(request):
    """
    API endpoint to get dynamic price for a flight.
    
    GET params:
        - flight_id: ID of the flight
        - seat_class: 'economy', 'business', or 'first'
        - departure_date: Date in YYYY-MM-DD format
    
    Returns JSON with base_price, dynamic_price, demand_level, etc.
    """
    flight_id = request.GET.get('flight_id')
    seat_class = request.GET.get('seat_class', 'economy')
    departure_date = request.GET.get('departure_date')
    
    if not flight_id or not departure_date:
        return JsonResponse({'error': 'Missing flight_id or departure_date'}, status=400)
    
    try:
        flight = Flight.objects.get(id=flight_id)
        pricing = get_dynamic_price(flight, seat_class, departure_date)
        
        return JsonResponse({
            'success': True,
            'flight_id': flight_id,
            'seat_class': seat_class,
            'base_price': pricing['base_price'],
            'dynamic_price': pricing['dynamic_price'],
            'multiplier': pricing['multiplier'],
            'demand_level': pricing['demand_level'],
            'occupancy': pricing['occupancy'],
            'days_to_departure': pricing['days_to_departure'],
            'savings': pricing['savings']
        })
    except Flight.DoesNotExist:
        return JsonResponse({'error': 'Flight not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_flight_pricing(request):
    """
    API endpoint to get dynamic prices for multiple flights.
    
    POST body:
        - flight_ids: List of flight IDs
        - seat_class: 'economy', 'business', or 'first'
        - departure_date: Date in YYYY-MM-DD format
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        flight_ids = data.get('flight_ids', [])
        seat_class = data.get('seat_class', 'economy')
        departure_date = data.get('departure_date')
        
        if not departure_date:
            return JsonResponse({'error': 'departure_date required'}, status=400)
        
        results = {}
        for flight_id in flight_ids:
            try:
                flight = Flight.objects.get(id=flight_id)
                pricing = get_dynamic_price(flight, seat_class, departure_date)
                results[str(flight_id)] = pricing
            except Flight.DoesNotExist:
                results[str(flight_id)] = {'error': 'Not found'}
        
        return JsonResponse({'success': True, 'prices': results})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
