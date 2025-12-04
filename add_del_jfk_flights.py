"""
Script to add Delhi to New York flights.
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

def add_del_jfk_flights():
    """Add flights between Delhi and New York JFK."""
    
    try:
        delhi = Place.objects.get(code='DEL')
        jfk = Place.objects.get(code='JFK')
    except Place.DoesNotExist as e:
        print(f"Error: {e}")
        return
    
    # Airlines that fly DEL-JFK route
    airlines = [
        ('AI', 'Air India', 'Boeing 777-300ER'),
        ('AA', 'American Airlines', 'Boeing 777-200'),
        ('DL', 'Delta Airlines', 'Airbus A350-900'),
        ('UA', 'United Airlines', 'Boeing 787-9'),
    ]
    
    # Flight schedules DEL -> JFK (typical flight duration: 15-16 hours)
    del_jfk_schedules = [
        (time(1, 30), 15.5, 'Morning Arrival'),   # Depart 1:30 AM, arrive ~11 AM local
        (time(14, 0), 15.5, 'Evening Arrival'),   # Depart 2 PM, arrive ~8 PM local
        (time(22, 30), 16.0, 'Afternoon Arrival'), # Depart 10:30 PM, arrive ~3 PM local
    ]
    
    # Flight schedules JFK -> DEL (typical flight duration: 14-15 hours)
    jfk_del_schedules = [
        (time(10, 30), 14.5, 'Evening Arrival'),  # Depart 10:30 AM, arrive ~11 PM local
        (time(22, 0), 14.0, 'Afternoon Arrival'),  # Depart 10 PM, arrive ~10 PM next day local
        (time(23, 55), 14.5, 'Evening Arrival'),   # Depart 11:55 PM, arrive ~12 AM+2 local
    ]
    
    flights_added = 0
    
    # Add DEL -> JFK flights
    print("Adding DEL -> JFK flights...")
    for weekday in range(7):  # All days of the week
        week_obj = Week.objects.get(number=weekday)
        
        for depart_time, duration_hours, note in del_jfk_schedules:
            airline_code, airline_name, plane = random.choice(airlines)
            
            duration = timedelta(hours=duration_hours)
            
            # Calculate arrival time (accounting for time zone - JFK is UTC-5, DEL is UTC+5:30)
            # Effective time difference is about -10.5 hours
            arrival_hour = (depart_time.hour + int(duration_hours) - 10) % 24  # Simplified
            arrival_time = time(arrival_hour, depart_time.minute)
            
            # Fares for long-haul international flight
            economy_fare = random.randint(55000, 85000)
            business_fare = round(economy_fare * random.uniform(2.8, 3.5))
            first_fare = round(economy_fare * random.uniform(5.0, 7.0))
            
            flight_no = f"{airline_code}{random.randint(100, 999)}"
            
            flight = Flight.objects.create(
                origin=delhi,
                destination=jfk,
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
            print(f"  Added: {airline_name} {flight_no} DEL {depart_time.strftime('%H:%M')} -> JFK (₹{economy_fare:,})")
    
    # Add JFK -> DEL flights
    print("\nAdding JFK -> DEL flights...")
    for weekday in range(7):
        week_obj = Week.objects.get(number=weekday)
        
        for depart_time, duration_hours, note in jfk_del_schedules:
            airline_code, airline_name, plane = random.choice(airlines)
            
            duration = timedelta(hours=duration_hours)
            
            # Calculate arrival time (JFK to DEL, add ~10.5 hours for time zone)
            arrival_hour = (depart_time.hour + int(duration_hours) + 10) % 24
            arrival_time = time(arrival_hour, depart_time.minute)
            
            # Fares
            economy_fare = random.randint(55000, 85000)
            business_fare = round(economy_fare * random.uniform(2.8, 3.5))
            first_fare = round(economy_fare * random.uniform(5.0, 7.0))
            
            flight_no = f"{airline_code}{random.randint(100, 999)}"
            
            flight = Flight.objects.create(
                origin=jfk,
                destination=delhi,
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
            print(f"  Added: {airline_name} {flight_no} JFK {depart_time.strftime('%H:%M')} -> DEL (₹{economy_fare:,})")
    
    print(f"\n✅ Total flights added: {flights_added}")
    print(f"   DEL -> JFK: {len(del_jfk_schedules) * 7} flights")
    print(f"   JFK -> DEL: {len(jfk_del_schedules) * 7} flights")
    
    # Verify
    del_jfk_count = Flight.objects.filter(origin=delhi, destination=jfk).count()
    jfk_del_count = Flight.objects.filter(origin=jfk, destination=delhi).count()
    print(f"\n📊 Total flights in database:")
    print(f"   DEL -> JFK: {del_jfk_count}")
    print(f"   JFK -> DEL: {jfk_del_count}")

if __name__ == "__main__":
    add_del_jfk_flights()
