"""
Dynamic Pricing Module for Flight Booking System

This module implements demand-based dynamic pricing where prices adjust based on:
1. Seat occupancy rate (higher occupancy = higher prices)
2. Time to departure (closer to departure = higher prices)

Price Multiplier Formula:
- Base multiplier starts at 1.0
- Occupancy factor: 0.85x (low demand) to 1.50x (high demand)
- Time factor: 0.90x (early booking) to 1.30x (last minute)
"""

from datetime import datetime, date, timedelta
from django.db.models import Count, Q
import logging

logger = logging.getLogger(__name__)


def get_seat_occupancy(flight, flight_date):
    """
    Calculate the seat occupancy rate for a specific flight on a given date.
    
    Returns: float between 0.0 and 1.0 representing occupancy percentage
    """
    from .models import Seat, Ticket
    
    # Count total seats for this flight
    total_seats = Seat.objects.filter(flight=flight).count()
    
    if total_seats == 0:
        # If no seats configured, estimate based on tickets
        confirmed_tickets = Ticket.objects.filter(
            flight=flight,
            flight_ddate=flight_date,
            status='CONFIRMED'
        ).count()
        # Assume average 200 seats per flight
        total_seats = 200
        occupied_seats = confirmed_tickets
    else:
        # Count occupied seats (booked + reserved)
        occupied_seats = Seat.objects.filter(
            flight=flight,
            status__in=['booked', 'reserved']
        ).count()
    
    if total_seats == 0:
        return 0.0
    
    occupancy = occupied_seats / total_seats
    logger.info(f"[DYNAMIC PRICING] Flight {flight.id} occupancy: {occupied_seats}/{total_seats} = {occupancy:.2%}")
    return min(occupancy, 1.0)  # Cap at 100%


def get_days_to_departure(departure_date):
    """
    Calculate days remaining until departure.
    
    Returns: int (number of days)
    """
    if isinstance(departure_date, str):
        departure_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
    elif isinstance(departure_date, datetime):
        departure_date = departure_date.date()
    
    today = date.today()
    delta = (departure_date - today).days
    return max(delta, 0)


def get_occupancy_multiplier(occupancy_rate):
    """
    Calculate price multiplier based on seat occupancy.
    
    Occupancy Tiers:
    - < 30%: 0.85x (15% discount to attract bookings)
    - 30-50%: 1.00x (base price)
    - 50-70%: 1.15x (15% increase)
    - 70-85%: 1.30x (30% increase, high demand)
    - > 85%: 1.50x (50% surge pricing)
    """
    if occupancy_rate < 0.30:
        multiplier = 0.85
        tier = "LOW DEMAND (discount)"
    elif occupancy_rate < 0.50:
        multiplier = 1.00
        tier = "NORMAL"
    elif occupancy_rate < 0.70:
        multiplier = 1.15
        tier = "MODERATE DEMAND"
    elif occupancy_rate < 0.85:
        multiplier = 1.30
        tier = "HIGH DEMAND"
    else:
        multiplier = 1.50
        tier = "SURGE PRICING"
    
    logger.info(f"[DYNAMIC PRICING] Occupancy {occupancy_rate:.2%} → Multiplier: {multiplier}x ({tier})")
    return multiplier


def get_time_multiplier(days_to_departure):
    """
    Calculate price multiplier based on time to departure.
    
    Time Tiers:
    - > 30 days: 0.90x (early bird discount)
    - 15-30 days: 1.00x (base price)
    - 7-14 days: 1.10x (moderate increase)
    - 3-6 days: 1.20x (last week premium)
    - < 3 days: 1.30x (last minute surge)
    """
    if days_to_departure > 30:
        multiplier = 0.90
        tier = "EARLY BIRD"
    elif days_to_departure >= 15:
        multiplier = 1.00
        tier = "NORMAL"
    elif days_to_departure >= 7:
        multiplier = 1.10
        tier = "MODERATE URGENCY"
    elif days_to_departure >= 3:
        multiplier = 1.20
        tier = "LAST WEEK"
    else:
        multiplier = 1.30
        tier = "LAST MINUTE"
    
    logger.info(f"[DYNAMIC PRICING] {days_to_departure} days to departure → Multiplier: {multiplier}x ({tier})")
    return multiplier


def get_dynamic_price(flight, seat_class, departure_date):
    """
    Calculate the dynamic price for a flight.
    
    Args:
        flight: Flight model instance
        seat_class: 'economy', 'business', or 'first'
        departure_date: Date of departure
    
    Returns:
        dict with 'base_price', 'dynamic_price', 'multiplier', 'savings'
    """
    # Get base fare based on seat class
    if seat_class.lower() == 'economy':
        base_price = flight.economy_fare or 0
    elif seat_class.lower() == 'business':
        base_price = flight.business_fare or 0
    elif seat_class.lower() == 'first':
        base_price = flight.first_fare or 0
    else:
        base_price = flight.economy_fare or 0
    
    if base_price == 0:
        logger.warning(f"[DYNAMIC PRICING] No base price for flight {flight.id} ({seat_class})")
        return {
            'base_price': 0,
            'dynamic_price': 0,
            'multiplier': 1.0,
            'savings': 0,
            'demand_level': 'N/A'
        }
    
    # Calculate multipliers
    occupancy = get_seat_occupancy(flight, departure_date)
    days_to_dept = get_days_to_departure(departure_date)
    
    occupancy_mult = get_occupancy_multiplier(occupancy)
    time_mult = get_time_multiplier(days_to_dept)
    
    # Final multiplier is the product of both factors
    total_multiplier = occupancy_mult * time_mult
    
    # Calculate dynamic price
    dynamic_price = round(base_price * total_multiplier, 2)
    
    # Determine demand level for display
    if occupancy < 0.30:
        demand_level = 'Low'
    elif occupancy < 0.50:
        demand_level = 'Normal'
    elif occupancy < 0.70:
        demand_level = 'Moderate'
    elif occupancy < 0.85:
        demand_level = 'High'
    else:
        demand_level = 'Very High'
    
    # Calculate savings (positive = discount, negative = increase)
    price_diff = base_price - dynamic_price
    
    logger.info(f"[DYNAMIC PRICING] Flight {flight.id} ({seat_class}): "
                f"Base ${base_price:.2f} × {total_multiplier:.2f} = ${dynamic_price:.2f} "
                f"(Demand: {demand_level})")
    
    return {
        'base_price': base_price,
        'dynamic_price': dynamic_price,
        'multiplier': round(total_multiplier, 2),
        'savings': round(price_diff, 2),
        'demand_level': demand_level,
        'occupancy': round(occupancy * 100, 1),
        'days_to_departure': days_to_dept
    }


def get_flight_prices_with_dynamic(flights, seat_class, departure_date):
    """
    Get dynamic prices for multiple flights.
    
    Returns list of dicts with flight and pricing info.
    """
    results = []
    for flight in flights:
        pricing = get_dynamic_price(flight, seat_class, departure_date)
        results.append({
            'flight': flight,
            'pricing': pricing
        })
    return results
