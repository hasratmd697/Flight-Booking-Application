from .models import Flight, Seat, SEAT_CLASS
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone


def create_seats_for_flight(flight):
    """
    Create seats for a flight based on standard aircraft configuration
    """
    seats = []
    
    # Economy Class: Rows 1-25, Seats A-F (6 seats per row)
    economy_rows = range(1, 26)
    economy_columns = ['A', 'B', 'C', 'D', 'E', 'F']
    
    for row in economy_rows:
        for col in economy_columns:
            seat_number = f"{row}{col}"
            seats.append(Seat(
                flight=flight,
                seat_number=seat_number,
                seat_class='economy',
                status='available',
                price=flight.economy_fare if flight.economy_fare else 0
            ))
    
    # Business Class: Rows 26-30, Seats A-D (4 seats per row)
    business_rows = range(26, 31)
    business_columns = ['A', 'B', 'C', 'D']
    
    if flight.business_fare and flight.business_fare > 0:
        for row in business_rows:
            for col in business_columns:
                seat_number = f"{row}{col}"
                seats.append(Seat(
                    flight=flight,
                    seat_number=seat_number,
                    seat_class='business',
                    status='available',
                    price=flight.business_fare
                ))
    
    # First Class: Rows 31-33, Seats A-B (2 seats per row)
    first_rows = range(31, 34)
    first_columns = ['A', 'B']
    
    if flight.first_fare and flight.first_fare > 0:
        for row in first_rows:
            for col in first_columns:
                seat_number = f"{row}{col}"
                seats.append(Seat(
                    flight=flight,
                    seat_number=seat_number,
                    seat_class='first',
                    status='available',
                    price=flight.first_fare
                ))
    
    # Bulk create all seats
    Seat.objects.bulk_create(seats)
    return len(seats)


def get_seat_map(flight, seat_class='economy'):
    """
    Get seat map for a specific flight and class
    Returns a structured representation of the seat layout
    """
    seats = Seat.objects.filter(
        flight=flight,
        seat_class=seat_class
    ).select_for_update()
    
    # Organize seats by row
    seat_map = {}
    for seat in seats:
        row = ''.join(filter(str.isdigit, seat.seat_number))
        col = ''.join(filter(str.isalpha, seat.seat_number))
        
        if row not in seat_map:
            seat_map[row] = {}
        
        seat_map[row][col] = {
            'id': seat.id,
            'number': seat.seat_number,
            'status': seat.status,
            'price': seat.price,
            'reserved_until': seat.reserved_until
        }
    
    return seat_map


@transaction.atomic
def reserve_seat(seat_id, duration_minutes=10):
    """
    Reserve a seat temporarily with row-level locking to prevent race conditions
    """
    try:
        # Get the seat with row-level lock (SELECT FOR UPDATE)
        seat = Seat.objects.select_for_update().get(id=seat_id)
        
        # Check if seat is available
        if seat.status != 'available':
            # Check if reservation expired
            if seat.status == 'reserved' and seat.reserved_until:
                if timezone.now() > seat.reserved_until:
                    # Reservation expired, make it available
                    seat.status = 'available'
                    seat.reserved_until = None
                else:
                    return {'success': False, 'error': 'Seat is already reserved'}
            else:
                return {'success': False, 'error': 'Seat is not available'}
        
        # Reserve the seat
        seat.status = 'reserved'
        seat.reserved_until = timezone.now() + timedelta(minutes=duration_minutes)
        seat.save()
        
        return {
            'success': True,
            'seat_id': seat.id,
            'seat_number': seat.seat_number,
            'reserved_until': seat.reserved_until
        }
    except Seat.DoesNotExist:
        return {'success': False, 'error': 'Seat not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@transaction.atomic
def book_seat(seat_id):
    """
    Book a seat (mark as booked) with row-level locking
    """
    try:
        seat = Seat.objects.select_for_update().get(id=seat_id)
        
        # Can only book if available or reserved
        if seat.status not in ['available', 'reserved']:
            return {'success': False, 'error': 'Seat is not available for booking'}
        
        seat.status = 'booked'
        seat.reserved_until = None
        seat.save()
        
        return {'success': True, 'seat_id': seat.id, 'seat_number': seat.seat_number}
    except Seat.DoesNotExist:
        return {'success': False, 'error': 'Seat not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@transaction.atomic
def release_seat(seat_id):
    """
    Release a reserved seat back to available
    """
    try:
        seat = Seat.objects.select_for_update().get(id=seat_id)
        
        if seat.status == 'reserved':
            seat.status = 'available'
            seat.reserved_until = None
            seat.save()
            return {'success': True}
        
        return {'success': False, 'error': 'Seat is not reserved'}
    except Seat.DoesNotExist:
        return {'success': False, 'error': 'Seat not found'}


def cleanup_expired_reservations():
    """
    Clean up expired seat reservations (to be run periodically)
    """
    expired_seats = Seat.objects.filter(
        status='reserved',
        reserved_until__lt=timezone.now()
    )
    
    count = expired_seats.update(
        status='available',
        reserved_until=None
    )
    
    return count
