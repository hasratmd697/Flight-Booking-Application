"""
Comprehensive Test Suite for Flight Booking Application

This module contains test cases for:
- Models (User, Place, Week, Flight, Seat, Passenger, Ticket)
- Views (authentication, flight search, booking, seat selection)
- Seat Manager (seat reservation and booking logic)
- API Endpoints (AJAX endpoints for seat operations)
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, time
import json

from .models import Place, Week, Flight, Seat, Passenger, Ticket
from .seat_manager import (
    create_seats_for_flight, 
    reserve_seat, 
    book_seat, 
    release_seat,
    cleanup_expired_reservations,
    get_seat_map
)

User = get_user_model()


class ModelTestCase(TestCase):
    """Test cases for Django models"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Get or create test places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'John F Kennedy International Airport',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'Los Angeles International Airport',
                'country': 'USA'
            }
        )
        
        # Create week days
        self.monday = Week.objects.create(number=0, name='Monday')
        self.tuesday = Week.objects.create(number=1, name='Tuesday')
        
        # Create test flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5, minutes=30),
            arrival_time=time(15, 30),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00,
            business_fare=500.00,
            first_fare=1000.00
        )
        self.flight.depart_day.add(self.monday)
    
    def test_user_creation(self):
        """Test user model creation and string representation"""
        self.assertEqual(str(self.user), f"{self.user.id}: Test User")
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_place_creation(self):
        """Test place model creation and string representation"""
        # Use assertIn for flexibility - Place might exist from CSV with different country format
        origin_str = str(self.origin)
        self.assertIn('New York', origin_str)
        self.assertIn('JFK', origin_str)
        self.assertEqual(self.origin.code, 'JFK')
    
    def test_week_creation(self):
        """Test week model creation and string representation"""
        self.assertEqual(str(self.monday), "Monday (0)")
        self.assertEqual(self.monday.number, 0)
    
    def test_flight_creation(self):
        """Test flight model creation and string representation"""
        self.assertIn('JFK', str(self.flight))
        self.assertIn('LAX', str(self.flight))
        self.assertEqual(self.flight.economy_fare, 250.00)
    
    def test_seat_creation(self):
        """Test seat model creation"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='1A',
            seat_class='economy',
            status='available',
            price=250.00
        )
        self.assertEqual(str(seat), f"{self.flight.id} - Seat 1A (economy)")
        self.assertEqual(seat.status, 'available')
    
    def test_passenger_creation(self):
        """Test passenger model creation"""
        passenger = Passenger.objects.create(
            first_name='John',
            last_name='Doe',
            gender='male'
        )
        self.assertEqual(str(passenger), "Passenger: John Doe, male")
    
    def test_ticket_creation(self):
        """Test ticket model creation"""
        passenger = Passenger.objects.create(
            first_name='John',
            last_name='Doe',
            gender='male'
        )
        ticket = Ticket.objects.create(
            user=self.user,
            ref_no='ABC123',
            flight=self.flight,
            flight_ddate=datetime.now().date(),
            flight_adate=datetime.now().date(),
            flight_fare=250.00,
            other_charges=50.00,
            total_fare=300.00,
            seat_class='economy',
            status='PENDING',
            mobile='+1 1234567890',
            email='test@example.com'
        )
        ticket.passengers.add(passenger)
        self.assertEqual(str(ticket), 'ABC123')
        self.assertEqual(ticket.status, 'PENDING')


class AuthenticationTestCase(TestCase):
    """Test cases for authentication views"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertRedirects(response, reverse('index'))
    
    def test_login_failure(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username and/or password')
    
    def test_register_page_loads(self):
        """Test that register page loads correctly"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
    
    def test_register_success(self):
        """Test successful registration"""
        response = self.client.post(reverse('register'), {
            'firstname': 'New',
            'lastname': 'User',
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirmation': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(reverse('register'), {
            'firstname': 'New',
            'lastname': 'User',
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'newpass123',
            'confirmation': 'differentpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords must match')
    
    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_already_logged_in_redirects(self):
        """Test that logged in users accessing login page are redirected"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)


class IndexViewTestCase(TestCase):
    """Test cases for index/home page"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_index_page_loads(self):
        """Test that index page loads correctly"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
    
    def test_index_has_date_constraints(self):
        """Test that index page has min and max date constraints"""
        response = self.client.get(reverse('index'))
        self.assertIn('min_date', response.context)
        self.assertIn('max_date', response.context)
    
    def test_index_post_one_way_trip(self):
        """Test index POST for one-way trip"""
        response = self.client.post(reverse('index'), {
            'Origin': 'JFK',
            'Destination': 'LAX',
            'DepartDate': '2025-12-15',
            'SeatClass': 'Economy',
            'TripType': '1'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['trip_type'], '1')
    
    def test_index_post_round_trip(self):
        """Test index POST for round trip"""
        response = self.client.post(reverse('index'), {
            'Origin': 'JFK',
            'Destination': 'LAX',
            'DepartDate': '2025-12-15',
            'ReturnDate': '2025-12-20',
            'SeatClass': 'Economy',
            'TripType': '2'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['trip_type'], '2')


class FlightSearchTestCase(TestCase):
    """Test cases for flight search functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'John F Kennedy International Airport',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'Los Angeles International Airport',
                'country': 'USA'
            }
        )
        
        # Clear any existing Week objects and create fresh ones to avoid duplicates
        Week.objects.all().delete()
        for i, name in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
            Week.objects.create(number=i, name=name)
        
        # Create test flight for Monday
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5, minutes=30),
            arrival_time=time(15, 30),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00,
            business_fare=500.00,
            first_fare=1000.00
        )
        self.flight.depart_day.add(Week.objects.get(number=0))  # Monday
    
    def test_flight_search_valid_airports(self):
        """Test flight search with valid airport codes"""
        # Get a Monday date
        today = datetime.now().date()
        days_until_monday = (0 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        response = self.client.get(reverse('flight'), {
            'Origin': 'JFK',
            'Destination': 'LAX',
            'DepartDate': next_monday.strftime('%Y-%m-%d'),
            'SeatClass': 'economy',
            'TripType': '1'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_flight_search_invalid_origin(self):
        """Test flight search with invalid origin airport code"""
        response = self.client.get(reverse('flight'), {
            'Origin': 'INVALID',
            'Destination': 'LAX',
            'DepartDate': '2025-12-15',
            'SeatClass': 'economy',
            'TripType': '1'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid Origin Airport')
    
    def test_flight_search_invalid_destination(self):
        """Test flight search with invalid destination airport code"""
        response = self.client.get(reverse('flight'), {
            'Origin': 'JFK',
            'Destination': 'INVALID',
            'DepartDate': '2025-12-15',
            'SeatClass': 'economy',
            'TripType': '1'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid Destination Airport')
    
    def test_flight_search_nyc_suggestion(self):
        """Test that NYC code shows suggestion for JFK"""
        response = self.client.get(reverse('flight'), {
            'Origin': 'NYC',
            'Destination': 'LAX',
            'DepartDate': '2025-12-15',
            'SeatClass': 'economy',
            'TripType': '1'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'JFK')


class PlaceQueryTestCase(TestCase):
    """Test cases for place query/autocomplete"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'John F Kennedy International Airport',
                'country': 'USA'
            }
        )
        Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'Los Angeles International Airport',
                'country': 'USA'
            }
        )
    
    def test_query_by_city(self):
        """Test place query by city name"""
        response = self.client.get(reverse('query', args=['new']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['code'], 'JFK')
    
    def test_query_by_code(self):
        """Test place query by airport code"""
        response = self.client.get(reverse('query', args=['lax']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['code'], 'LAX')
    
    def test_query_no_results(self):
        """Test place query with no matching results"""
        response = self.client.get(reverse('query', args=['xyz123']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)


class SeatManagerTestCase(TestCase):
    """Test cases for seat manager functions"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5),
            arrival_time=time(15, 0),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00,
            business_fare=500.00,
            first_fare=1000.00
        )
    
    def test_create_seats_for_flight(self):
        """Test seat creation for a flight"""
        count = create_seats_for_flight(self.flight)
        
        # Economy: 25 rows * 6 seats = 150
        economy_count = Seat.objects.filter(flight=self.flight, seat_class='economy').count()
        self.assertEqual(economy_count, 150)
        
        # Business: 5 rows * 4 seats = 20
        business_count = Seat.objects.filter(flight=self.flight, seat_class='business').count()
        self.assertEqual(business_count, 20)
        
        # First: 3 rows * 2 seats = 6
        first_count = Seat.objects.filter(flight=self.flight, seat_class='first').count()
        self.assertEqual(first_count, 6)
    
    def test_reserve_seat_success(self):
        """Test successful seat reservation"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='1A',
            seat_class='economy',
            status='available',
            price=250.00
        )
        
        result = reserve_seat(seat.id, duration_minutes=10)
        self.assertTrue(result['success'])
        
        seat.refresh_from_db()
        self.assertEqual(seat.status, 'reserved')
        self.assertIsNotNone(seat.reserved_until)
    
    def test_reserve_seat_already_booked(self):
        """Test reservation of already booked seat"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='1B',
            seat_class='economy',
            status='booked',
            price=250.00
        )
        
        result = reserve_seat(seat.id)
        self.assertFalse(result['success'])
        self.assertIn('not available', result['error'])
    
    def test_reserve_seat_already_reserved(self):
        """Test reservation of already reserved seat"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='1C',
            seat_class='economy',
            status='reserved',
            price=250.00,
            reserved_until=timezone.now() + timedelta(minutes=5)
        )
        
        result = reserve_seat(seat.id)
        self.assertFalse(result['success'])
        self.assertIn('already reserved', result['error'])
    
    def test_reserve_expired_seat(self):
        """Test that expired reservation can be re-reserved"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='1D',
            seat_class='economy',
            status='reserved',
            price=250.00,
            reserved_until=timezone.now() - timedelta(minutes=5)  # Expired
        )
        
        result = reserve_seat(seat.id)
        self.assertTrue(result['success'])
    
    def test_book_seat_success(self):
        """Test successful seat booking"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='2A',
            seat_class='economy',
            status='available',
            price=250.00
        )
        
        result = book_seat(seat.id)
        self.assertTrue(result['success'])
        
        seat.refresh_from_db()
        self.assertEqual(seat.status, 'booked')
    
    def test_book_reserved_seat(self):
        """Test booking a reserved seat"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='2B',
            seat_class='economy',
            status='reserved',
            price=250.00,
            reserved_until=timezone.now() + timedelta(minutes=5)
        )
        
        result = book_seat(seat.id)
        self.assertTrue(result['success'])
        
        seat.refresh_from_db()
        self.assertEqual(seat.status, 'booked')
    
    def test_release_seat_success(self):
        """Test successful seat release"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='3A',
            seat_class='economy',
            status='reserved',
            price=250.00,
            reserved_until=timezone.now() + timedelta(minutes=5)
        )
        
        result = release_seat(seat.id)
        self.assertTrue(result['success'])
        
        seat.refresh_from_db()
        self.assertEqual(seat.status, 'available')
        self.assertIsNone(seat.reserved_until)
    
    def test_release_non_reserved_seat(self):
        """Test release of non-reserved seat"""
        seat = Seat.objects.create(
            flight=self.flight,
            seat_number='3B',
            seat_class='economy',
            status='available',
            price=250.00
        )
        
        result = release_seat(seat.id)
        self.assertFalse(result['success'])
    
    def test_cleanup_expired_reservations(self):
        """Test cleanup of expired reservations"""
        # Create some expired seats
        for i in range(3):
            Seat.objects.create(
                flight=self.flight,
                seat_number=f'4{chr(65+i)}',
                seat_class='economy',
                status='reserved',
                price=250.00,
                reserved_until=timezone.now() - timedelta(minutes=10)  # Expired
            )
        
        count = cleanup_expired_reservations()
        self.assertEqual(count, 3)
        
        # Verify seats are now available
        available_count = Seat.objects.filter(
            flight=self.flight,
            status='available',
            seat_number__startswith='4'
        ).count()
        self.assertEqual(available_count, 3)
    
    def test_get_seat_map(self):
        """Test get_seat_map function"""
        create_seats_for_flight(self.flight)
        
        seat_map = get_seat_map(self.flight, seat_class='economy')
        
        # Check that row 1 exists
        self.assertIn('1', seat_map)
        # Check that columns A-F exist in row 1
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            self.assertIn(col, seat_map['1'])


class SeatAPITestCase(TestCase):
    """Test cases for seat API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5),
            arrival_time=time(15, 0),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00,
            business_fare=500.00,
            first_fare=1000.00
        )
        
        # Create seats
        create_seats_for_flight(self.flight)
    
    def test_get_available_seats(self):
        """Test get available seats API"""
        response = self.client.get(reverse('available_seats'), {
            'flight_id': self.flight.id,
            'seat_class': 'economy'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('seats', data)
    
    def test_get_available_seats_invalid_flight(self):
        """Test get available seats with invalid flight ID"""
        response = self.client.get(reverse('available_seats'), {
            'flight_id': 99999,
            'seat_class': 'economy'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_reserve_seat_api(self):
        """Test reserve seat API"""
        seat = Seat.objects.filter(flight=self.flight, seat_class='economy').first()
        
        response = self.client.post(
            reverse('reserve_seat'),
            json.dumps({'seat_id': seat.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_reserve_seat_api_no_seat_id(self):
        """Test reserve seat API without seat ID"""
        response = self.client.post(
            reverse('reserve_seat'),
            json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_release_seat_api(self):
        """Test release seat API"""
        seat = Seat.objects.filter(flight=self.flight, seat_class='economy').first()
        seat.status = 'reserved'
        seat.reserved_until = timezone.now() + timedelta(minutes=10)
        seat.save()
        
        response = self.client.post(
            reverse('release_seat'),
            json.dumps({'seat_id': seat.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_confirm_booking_unauthenticated(self):
        """Test confirm booking requires authentication"""
        seat = Seat.objects.filter(flight=self.flight, seat_class='economy').first()
        
        response = self.client.post(
            reverse('confirm_booking'),
            json.dumps({'seat_ids': [seat.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('not authenticated', data['error'])
    
    def test_confirm_booking_authenticated(self):
        """Test confirm booking when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        seat = Seat.objects.filter(flight=self.flight, seat_class='economy').first()
        
        response = self.client.post(
            reverse('confirm_booking'),
            json.dumps({'seat_ids': [seat.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])


class BookingFlowTestCase(TestCase):
    """Test cases for the complete booking flow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Clear any existing Week objects and create fresh ones to avoid duplicates
        Week.objects.all().delete()
        for i, name in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
            Week.objects.create(number=i, name=name)
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5, minutes=30),
            arrival_time=time(15, 30),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00,
            business_fare=500.00,
            first_fare=1000.00
        )
        self.flight.depart_day.add(Week.objects.get(number=0))
    
    def test_review_requires_authentication(self):
        """Test that review page requires authentication"""
        response = self.client.get(reverse('review'), {
            'flight1Id': self.flight.id,
            'flight1Date': '15-12-2025',
            'seatClass': 'Economy'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_review_authenticated(self):
        """Test review page when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('review'), {
            'flight1Id': self.flight.id,
            'flight1Date': '15-12-2025',
            'seatClass': 'Economy'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_book_requires_post(self):
        """Test that book endpoint requires POST method"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('book'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Method must be post')
    
    def test_bookings_requires_authentication(self):
        """Test that bookings page requires authentication"""
        response = self.client.get(reverse('bookings'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_bookings_authenticated(self):
        """Test bookings page when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('bookings'))
        self.assertEqual(response.status_code, 200)


class TicketCancellationTestCase(TestCase):
    """Test cases for ticket cancellation"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5),
            arrival_time=time(15, 0),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00
        )
        
        # Create ticket
        self.ticket = Ticket.objects.create(
            user=self.user,
            ref_no='ABC123',
            flight=self.flight,
            flight_ddate=datetime.now().date(),
            flight_fare=250.00,
            total_fare=300.00,
            seat_class='economy',
            status='CONFIRMED'
        )
    
    def test_cancel_ticket_success(self):
        """Test successful ticket cancellation"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('cancelticket'), {
            'ref': 'ABC123'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'CANCELLED')
    
    def test_cancel_ticket_unauthorized_user(self):
        """Test ticket cancellation by unauthorized user"""
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.post(reverse('cancelticket'), {
            'ref': 'ABC123'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_cancel_ticket_requires_post(self):
        """Test that cancel endpoint requires POST method"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cancelticket'))
        self.assertContains(response, 'Method must be POST')


class StaticPagesTestCase(TestCase):
    """Test cases for static pages"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_contact_page(self):
        """Test contact page loads"""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
    
    def test_privacy_policy_page(self):
        """Test privacy policy page loads"""
        response = self.client.get(reverse('privacypolicy'))
        self.assertEqual(response.status_code, 200)
    
    def test_terms_page(self):
        """Test terms and conditions page loads"""
        response = self.client.get(reverse('termsandconditions'))
        self.assertEqual(response.status_code, 200)
    
    def test_about_page(self):
        """Test about us page loads"""
        response = self.client.get(reverse('aboutus'))
        self.assertEqual(response.status_code, 200)


class SeatSelectionViewTestCase(TestCase):
    """Test cases for seat selection view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5),
            arrival_time=time(15, 0),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00,
            business_fare=500.00,
            first_fare=1000.00
        )
    
    def test_seat_selection_requires_authentication(self):
        """Test that seat selection requires authentication"""
        response = self.client.get(reverse('seat_selection'), {
            'flight_id': self.flight.id,
            'seat_class': 'economy',
            'depart_date': '15-12-2025'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_seat_selection_authenticated(self):
        """Test seat selection when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('seat_selection'), {
            'flight_id': self.flight.id,
            'seat_class': 'economy',
            'depart_date': '15-12-2025'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_seat_selection_creates_seats(self):
        """Test that seat selection creates seats if none exist"""
        self.client.login(username='testuser', password='testpass123')
        
        # Verify no seats initially
        self.assertEqual(Seat.objects.filter(flight=self.flight).count(), 0)
        
        response = self.client.get(reverse('seat_selection'), {
            'flight_id': self.flight.id,
            'seat_class': 'economy',
            'depart_date': '15-12-2025'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify seats were created
        self.assertGreater(Seat.objects.filter(flight=self.flight).count(), 0)
    
    def test_seat_selection_invalid_flight(self):
        """Test seat selection with invalid flight ID"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('seat_selection'), {
            'flight_id': 99999,
            'seat_class': 'economy',
            'depart_date': '15-12-2025'
        })
        self.assertEqual(response.status_code, 404)


class TicketDataAPITestCase(TestCase):
    """Test cases for ticket data API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5),
            arrival_time=time(15, 0),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00
        )
        
        # Create ticket
        self.ticket = Ticket.objects.create(
            user=self.user,
            ref_no='XYZ789',
            flight=self.flight,
            flight_ddate=datetime(2025, 12, 15).date(),
            flight_fare=250.00,
            total_fare=300.00,
            seat_class='economy',
            status='CONFIRMED'
        )
    
    def test_ticket_data_api(self):
        """Test ticket data API returns correct data"""
        response = self.client.get(reverse('ticketdata', args=['XYZ789']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['ref'], 'XYZ789')
        self.assertEqual(data['from'], 'JFK')
        self.assertEqual(data['to'], 'LAX')
        self.assertEqual(data['status'], 'CONFIRMED')


class SelectFlightViewTestCase(TestCase):
    """Test cases for select flight view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get or create places to avoid duplicates
        self.origin, _ = Place.objects.get_or_create(
            code='JFK',
            defaults={
                'city': 'New York',
                'airport': 'JFK',
                'country': 'USA'
            }
        )
        self.destination, _ = Place.objects.get_or_create(
            code='LAX',
            defaults={
                'city': 'Los Angeles',
                'airport': 'LAX',
                'country': 'USA'
            }
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            origin=self.origin,
            destination=self.destination,
            depart_time=time(10, 0),
            duration=timedelta(hours=5),
            arrival_time=time(15, 0),
            plane='Boeing 737',
            airline='Test Airlines',
            economy_fare=250.00
        )
    
    def test_select_flight_requires_authentication(self):
        """Test that select flight requires authentication"""
        response = self.client.get(reverse('select_flight'), {
            'flight1Id': self.flight.id,
            'flight1Date': '15-12-2025',
            'seatClass': 'economy'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_select_flight_redirects_to_seats(self):
        """Test that select flight redirects to seat selection"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('select_flight'), {
            'flight1Id': self.flight.id,
            'flight1Date': '15-12-2025',
            'seatClass': 'economy'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn('/flight/seats', response.url)
