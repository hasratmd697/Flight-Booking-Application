"""
Script to check and add missing airport codes.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from flight.models import Place

def check_places():
    """Check available places and their codes."""
    
    print("Current places in database:")
    places = Place.objects.all().order_by('code')
    print(f"Total: {places.count()}\n")
    
    codes = [p.code for p in places]
    
    # Common codes that users might search for
    common_codes = ['NYC', 'NRT', 'LAX', 'JFK', 'DEL', 'BOM', 'LHR', 'CDG', 'DXB', 'SIN', 'HKG', 'SYD', 'MEL']
    
    print("Checking common codes:")
    for code in common_codes:
        if code in codes:
            place = Place.objects.get(code=code)
            print(f"  ✓ {code}: {place.city}, {place.country}")
        else:
            print(f"  ✗ {code}: NOT FOUND")

def add_missing_places():
    """Add commonly used airport codes that might be missing."""
    
    # NYC is an alias for JFK - New York city has multiple airports
    # Some users search by city code rather than airport code
    
    missing_places = [
        # NYC area airports (NYC is often used as a city code)
        # NRT - Narita is in the database as Tokyo Narita
    ]
    
    # Check if NRT exists
    if not Place.objects.filter(code='NRT').exists():
        Place.objects.create(
            city='Tokyo',
            airport='Narita International Airport',
            code='NRT',
            country='Japan'
        )
        print("Added NRT (Narita)")
    else:
        print("NRT already exists")
    
    # NYC is a city code, not an actual airport code
    # JFK, LGA, EWR are the actual airport codes for NYC area
    # Let's check if they exist
    nyc_airports = ['JFK', 'LGA', 'EWR']
    for code in nyc_airports:
        if Place.objects.filter(code=code).exists():
            place = Place.objects.get(code=code)
            print(f"{code} already exists: {place.airport}")
        else:
            print(f"{code} not found")

if __name__ == "__main__":
    check_places()
    print("\n" + "="*50 + "\n")
    add_missing_places()
