"""
Script to update flight fares for Business and First class.
This script updates flights that have 0 business_fare or first_fare 
by calculating them based on the economy_fare.

Typical fare multipliers:
- Business Class: 2.5x to 3.5x economy fare
- First Class: 4x to 6x economy fare

Run this from the project root using:
python manage.py shell < update_flight_fares.py

Or run the update_fares management command:
python manage.py update_fares
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from flight.models import Flight
import random

def update_flight_fares():
    """Update flights with missing business and first class fares."""
    
    # Get all flights
    flights = Flight.objects.all()
    total_updated = 0
    
    print(f"Total flights in database: {flights.count()}")
    
    for flight in flights:
        updated = False
        economy = flight.economy_fare or 0
        
        if economy <= 0:
            continue
            
        # Update business fare if it's 0 or None
        if not flight.business_fare or flight.business_fare <= 0:
            # Business class is typically 2.5x to 3.5x economy
            multiplier = random.uniform(2.5, 3.5)
            flight.business_fare = round(economy * multiplier, 2)
            updated = True
            
        # Update first class fare if it's 0 or None
        if not flight.first_fare or flight.first_fare <= 0:
            # First class is typically 4x to 6x economy
            multiplier = random.uniform(4.0, 6.0)
            flight.first_fare = round(economy * multiplier, 2)
            updated = True
        
        if updated:
            flight.save()
            total_updated += 1
    
    print(f"Updated {total_updated} flights with business and first class fares.")
    
    # Show sample of updated flights
    print("\nSample flights with all fares:")
    sample_flights = Flight.objects.filter(economy_fare__gt=0, business_fare__gt=0, first_fare__gt=0)[:10]
    for f in sample_flights:
        print(f"  {f.origin.code} -> {f.destination.code} | Economy: ₹{f.economy_fare:,.0f} | Business: ₹{f.business_fare:,.0f} | First: ₹{f.first_fare:,.0f}")

if __name__ == "__main__":
    update_flight_fares()
