"""
Script to analyze and add missing flight routes.
"""

import os
import sys
import django
import random
from datetime import time, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from flight.models import Place, Flight, Week

def analyze_routes():
    """Analyze which routes have and don't have flights."""
    
    places = Place.objects.all()
    total_places = places.count()
    
    print(f"Total places: {total_places}")
    print(f"Total possible route combinations: {total_places * (total_places - 1)}")
    
    # Count routes with at least one flight
    routes_with_flights = set()
    flights = Flight.objects.all()
    
    for flight in flights:
        route = (flight.origin.code, flight.destination.code)
        routes_with_flights.add(route)
    
    print(f"Routes with flights: {len(routes_with_flights)}")
    
    # Show sample routes without flights
    print("\nSample routes WITHOUT flights:")
    count = 0
    for origin in places[:20]:
        for dest in places[:20]:
            if origin != dest:
                route = (origin.code, dest.code)
                if route not in routes_with_flights:
                    print(f"  {origin.code} ({origin.city}) -> {dest.code} ({dest.city})")
                    count += 1
                    if count >= 20:
                        break
        if count >= 20:
            break

def add_missing_routes():
    """Add flights for popular routes that are missing."""
    
    # Define popular routes that should have flights
    popular_routes = [
        # US domestic
        ('JFK', 'LAX'), ('LAX', 'JFK'),
        ('JFK', 'SFO'), ('SFO', 'JFK'),
        ('JFK', 'ORD'), ('ORD', 'JFK'),
        ('LAX', 'SFO'), ('SFO', 'LAX'),
        
        # India domestic
        ('DEL', 'BLR'), ('BLR', 'DEL'),
        ('BOM', 'BLR'), ('BLR', 'BOM'),
        ('DEL', 'CCU'), ('CCU', 'DEL'),
        ('BOM', 'CCU'), ('CCU', 'BOM'),
        ('DEL', 'HYD'), ('HYD', 'DEL'),
        ('BOM', 'HYD'), ('HYD', 'BOM'),
        ('DEL', 'GOI'), ('GOI', 'DEL'),
        
        # International popular
        ('JFK', 'LHR'), ('LHR', 'JFK'),
        ('JFK', 'CDG'), ('CDG', 'JFK'),
        ('LAX', 'NRT'), ('NRT', 'LAX'),
        ('LAX', 'HKG'), ('HKG', 'LAX'),
        ('DEL', 'DXB'), ('DXB', 'DEL'),
        ('DEL', 'SIN'), ('SIN', 'DEL'),
        ('BOM', 'DXB'), ('DXB', 'BOM'),
        ('DEL', 'LHR'), ('LHR', 'DEL'),
        ('DEL', 'NRT'), ('NRT', 'DEL'),
        ('BOM', 'LHR'), ('LHR', 'BOM'),
        ('SIN', 'HKG'), ('HKG', 'SIN'),
        ('DXB', 'LHR'), ('LHR', 'DXB'),
    ]
    
    airlines = [
        ('AI', 'Air India'),
        ('UK', 'Vistara'), 
        ('6E', 'IndiGo'),
        ('AA', 'American Airlines'),
        ('DL', 'Delta Airlines'),
        ('UA', 'United Airlines'),
        ('BA', 'British Airways'),
        ('EK', 'Emirates'),
        ('SQ', 'Singapore Airlines'),
    ]
    
    flights_added = 0
    
    for origin_code, dest_code in popular_routes:
        try:
            origin = Place.objects.get(code=origin_code)
            destination = Place.objects.get(code=dest_code)
            
            # Check if flights already exist for this route
            existing = Flight.objects.filter(origin=origin, destination=destination).count()
            
            if existing == 0:
                print(f"Adding flights for {origin_code} -> {dest_code}")
                
                # Add 3-5 flights per day for this route
                for weekday in range(7):  # All days
                    week_obj = Week.objects.get(number=weekday)
                    
                    # Add 2-4 flights per day
                    for i in range(random.randint(2, 4)):
                        airline_code, airline_name = random.choice(airlines)
                        
                        # Random departure time
                        hour = random.randint(5, 22)
                        minute = random.choice([0, 15, 30, 45])
                        depart_time = time(hour, minute)
                        
                        # Duration based on distance (rough estimate)
                        if origin.country == destination.country:
                            # Domestic
                            duration_hours = random.uniform(1.5, 4)
                        else:
                            # International
                            duration_hours = random.uniform(4, 14)
                        
                        duration = timedelta(hours=duration_hours)
                        
                        # Calculate arrival time
                        arrival_hour = (hour + int(duration_hours)) % 24
                        arrival_minute = minute
                        arrival_time = time(arrival_hour, arrival_minute)
                        
                        # Fares
                        if origin.country == destination.country:
                            economy_fare = random.randint(4000, 15000)
                        else:
                            economy_fare = random.randint(25000, 120000)
                        
                        business_fare = round(economy_fare * random.uniform(2.5, 3.5))
                        first_fare = round(economy_fare * random.uniform(4.0, 6.0))
                        
                        # Flight number
                        flight_no = f"{airline_code}{random.randint(100, 9999)}"
                        
                        flight = Flight.objects.create(
                            origin=origin,
                            destination=destination,
                            depart_time=depart_time,
                            duration=duration,
                            arrival_time=arrival_time,
                            plane=flight_no,
                            airline=airline_name,
                            economy_fare=economy_fare,
                            business_fare=business_fare,
                            first_fare=first_fare
                        )
                        flight.depart_day.add(week_obj)
                        flight.save()
                        flights_added += 1
        
        except Place.DoesNotExist:
            print(f"Place not found: {origin_code} or {dest_code}")
    
    print(f"\nTotal flights added: {flights_added}")

if __name__ == "__main__":
    print("=== Analyzing Routes ===\n")
    analyze_routes()
    print("\n=== Adding Missing Routes ===\n")
    add_missing_routes()
