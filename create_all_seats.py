"""
Management command to create seats for all flights
Run with: python main.py shell < create_all_seats.py
"""

from flight.models import Flight
from flight.seat_manager import create_seats_for_flight

# Get all flights
flights = Flight.objects.all()

print(f"Found {flights.count()} flights")

for flight in flights:
    # Check if seats already exist
    if not flight.seats.exists():
        count = create_seats_for_flight(flight)
        print(f"Created {count} seats for flight {flight.id}: {flight.origin} to {flight.destination}")
    else:
        print(f"Flight {flight.id} already has seats")

print("\nDone! All flights now have seats.")
