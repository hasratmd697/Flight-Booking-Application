"""
Script to verify flight fares in the database.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from flight.models import Flight

def verify_fares():
    """Verify that flights have proper fares for all classes."""
    
    total = Flight.objects.count()
    
    economy_ok = Flight.objects.exclude(economy_fare=0).count()
    business_ok = Flight.objects.exclude(business_fare=0).count()
    first_ok = Flight.objects.exclude(first_fare=0).count()
    
    print(f"Total flights: {total}")
    print(f"Flights with Economy fare > 0: {economy_ok} ({100*economy_ok/total:.1f}%)")
    print(f"Flights with Business fare > 0: {business_ok} ({100*business_ok/total:.1f}%)")
    print(f"Flights with First class fare > 0: {first_ok} ({100*first_ok/total:.1f}%)")
    
    # Check a few sample routes
    print("\n--- Sample Routes ---")
    sample_origins = ['DEL', 'BOM', 'ATL', 'LAX', 'DXB']
    sample_destinations = ['BOM', 'DEL', 'LAX', 'ORD', 'LHR']
    
    from flight.models import Place
    
    for origin_code, dest_code in zip(sample_origins, sample_destinations):
        try:
            origin = Place.objects.get(code=origin_code)
            dest = Place.objects.get(code=dest_code)
            
            economy_flights = Flight.objects.filter(origin=origin, destination=dest).exclude(economy_fare=0).count()
            business_flights = Flight.objects.filter(origin=origin, destination=dest).exclude(business_fare=0).count()
            first_flights = Flight.objects.filter(origin=origin, destination=dest).exclude(first_fare=0).count()
            
            print(f"{origin_code} -> {dest_code}: Economy: {economy_flights}, Business: {business_flights}, First: {first_flights}")
        except Place.DoesNotExist:
            print(f"Place {origin_code} or {dest_code} not found")

if __name__ == "__main__":
    verify_fares()
