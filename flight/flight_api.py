"""
Amadeus Flight API Integration Module

This module provides a clean interface to the Amadeus Flight Offers Search API,
enabling dynamic flight search for any airport combination and date.

For API documentation: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class FlightOffer:
    """
    Represents a flight offer from the Amadeus API.
    This class provides a consistent interface that matches the existing template expectations.
    """
    id: str
    origin_code: str
    origin_city: str
    destination_code: str
    destination_city: str
    depart_time: datetime
    arrival_time: datetime
    duration: timedelta
    airline: str
    airline_code: str
    flight_number: str
    economy_fare: float
    business_fare: float
    first_fare: float
    stops: int
    aircraft: str
    
    @property
    def formatted_duration(self) -> str:
        """Format duration as HH:MM"""
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"


class AmadeusFlightAPI:
    """
    Wrapper class for Amadeus Flight Offers Search API.
    
    Usage:
        api = AmadeusFlightAPI()
        if api.is_available():
            flights = api.search_flights('JFK', 'LAX', '2024-12-25', 'economy')
    """
    
    # Airline name mappings (Amadeus returns codes, we want names)
    AIRLINE_NAMES = {
        'AA': 'American Airlines',
        'UA': 'United Airlines',
        'DL': 'Delta Air Lines',
        'BA': 'British Airways',
        'LH': 'Lufthansa',
        'AF': 'Air France',
        'EK': 'Emirates',
        'QR': 'Qatar Airways',
        'SQ': 'Singapore Airlines',
        'CX': 'Cathay Pacific',
        'JL': 'Japan Airlines',
        'NH': 'ANA',
        'TK': 'Turkish Airlines',
        'EY': 'Etihad Airways',
        'QF': 'Qantas',
        'VS': 'Virgin Atlantic',
        'IB': 'Iberia',
        'KL': 'KLM',
        'LX': 'Swiss',
        'OS': 'Austrian Airlines',
        'AI': 'Air India',
        '6E': 'IndiGo',
        'SG': 'SpiceJet',
        'UK': 'Vistara',
        'G8': 'Go First',
        'I5': 'AirAsia India',
        'AC': 'Air Canada',
        'WN': 'Southwest Airlines',
        'B6': 'JetBlue',
        'AS': 'Alaska Airlines',
        'F9': 'Frontier Airlines',
        'NK': 'Spirit Airlines',
    }
    
    # Cabin class mappings
    CABIN_CLASS_MAP = {
        'economy': 'ECONOMY',
        'business': 'BUSINESS',
        'first': 'FIRST',
        'premium_economy': 'PREMIUM_ECONOMY'
    }
    
    def __init__(self):
        """Initialize the Amadeus client."""
        self._client = None
        self._enabled = getattr(settings, 'AMADEUS_ENABLED', False)
        self._client_id = getattr(settings, 'AMADEUS_CLIENT_ID', '')
        self._client_secret = getattr(settings, 'AMADEUS_CLIENT_SECRET', '')
        
    def _get_client(self):
        """Lazy initialization of Amadeus client."""
        if self._client is None and self._enabled:
            try:
                from amadeus import Client, ResponseError
                self._client = Client(
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    log_level='silent'  # Set to 'debug' for troubleshooting
                )
                logger.info("Amadeus client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Amadeus client: {e}")
                self._client = None
        return self._client
    
    def is_available(self) -> bool:
        """Check if the Amadeus API is available and properly configured."""
        if not self._enabled:
            logger.debug("Amadeus API is disabled")
            return False
        
        if not self._client_id or not self._client_secret:
            logger.warning("Amadeus API credentials not configured")
            return False
        
        return self._get_client() is not None
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        seat_class: str = 'economy',
        adults: int = 1,
        max_results: int = 20
    ) -> List[FlightOffer]:
        """
        Search for flight offers.
        
        Args:
            origin: Origin airport IATA code (e.g., 'JFK')
            destination: Destination airport IATA code (e.g., 'LAX')
            departure_date: Departure date in YYYY-MM-DD format
            seat_class: Cabin class ('economy', 'business', 'first')
            adults: Number of adult passengers
            max_results: Maximum number of results to return
            
        Returns:
            List of FlightOffer objects
        """
        client = self._get_client()
        if not client:
            logger.warning("Amadeus client not available, returning empty results")
            return []
        
        try:
            from amadeus import ResponseError
            
            # Map seat class to Amadeus travel class
            travel_class = self.CABIN_CLASS_MAP.get(seat_class.lower(), 'ECONOMY')
            
            logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}, class={travel_class}")
            
            response = client.shopping.flight_offers_search.get(
                originLocationCode=origin.upper(),
                destinationLocationCode=destination.upper(),
                departureDate=departure_date,
                adults=adults,
                travelClass=travel_class,
                max=max_results,
                currencyCode='INR'  # Use INR for Indian market
            )
            
            flights = self._parse_response(response.data, seat_class)
            logger.info(f"Found {len(flights)} flight offers")
            return flights
            
        except ResponseError as e:
            logger.error(f"Amadeus API error: {e.response.status_code} - {e.response.body}")
            return []
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return []
    
    def _parse_response(self, data: List[Dict[str, Any]], seat_class: str) -> List[FlightOffer]:
        """
        Parse Amadeus API response into FlightOffer objects.
        
        Args:
            data: Raw API response data
            seat_class: The requested seat class
            
        Returns:
            List of FlightOffer objects
        """
        flights = []
        
        for offer in data:
            try:
                # Get the first itinerary and first segment (direct or first leg)
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                first_segment = segments[0]
                last_segment = segments[-1]
                
                # Calculate total duration
                duration_str = itinerary['duration']  # Format: PT5H30M
                duration = self._parse_duration(duration_str)
                
                # Get price
                price = float(offer['price']['total'])
                
                # Map prices based on seat class (apply multipliers for other classes)
                if seat_class.lower() == 'economy':
                    economy_fare = price
                    business_fare = price * 2.5
                    first_fare = price * 4.0
                elif seat_class.lower() == 'business':
                    economy_fare = price / 2.5
                    business_fare = price
                    first_fare = price * 1.8
                else:  # first
                    economy_fare = price / 4.0
                    business_fare = price / 1.8
                    first_fare = price
                
                # Get airline info
                carrier_code = first_segment['carrierCode']
                airline_name = self.AIRLINE_NAMES.get(carrier_code, carrier_code)
                
                # Parse departure and arrival times
                depart_time = datetime.fromisoformat(first_segment['departure']['at'].replace('Z', '+00:00'))
                arrival_time = datetime.fromisoformat(last_segment['arrival']['at'].replace('Z', '+00:00'))
                
                flight = FlightOffer(
                    id=offer['id'],
                    origin_code=first_segment['departure']['iataCode'],
                    origin_city=first_segment['departure']['iataCode'],  # City will be looked up from Place model
                    destination_code=last_segment['arrival']['iataCode'],
                    destination_city=last_segment['arrival']['iataCode'],
                    depart_time=depart_time,
                    arrival_time=arrival_time,
                    duration=duration,
                    airline=airline_name,
                    airline_code=carrier_code,
                    flight_number=f"{carrier_code}{first_segment['number']}",
                    economy_fare=round(economy_fare, 2),
                    business_fare=round(business_fare, 2),
                    first_fare=round(first_fare, 2),
                    stops=len(segments) - 1,
                    aircraft=first_segment.get('aircraft', {}).get('code', 'Unknown')
                )
                flights.append(flight)
                
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Error parsing flight offer: {e}")
                continue
        
        return flights
    
    def _parse_duration(self, duration_str: str) -> timedelta:
        """
        Parse ISO 8601 duration format (PT5H30M) to timedelta.
        
        Args:
            duration_str: Duration string in ISO 8601 format
            
        Returns:
            timedelta object
        """
        import re
        
        hours = 0
        minutes = 0
        
        hours_match = re.search(r'(\d+)H', duration_str)
        if hours_match:
            hours = int(hours_match.group(1))
        
        minutes_match = re.search(r'(\d+)M', duration_str)
        if minutes_match:
            minutes = int(minutes_match.group(1))
        
        return timedelta(hours=hours, minutes=minutes)


# Convenience function for views
def search_flights_api(origin: str, destination: str, date: str, seat_class: str = 'economy') -> List[FlightOffer]:
    """
    Convenience function to search flights using the Amadeus API.
    
    Returns empty list if API is not available or fails.
    """
    api = AmadeusFlightAPI()
    if api.is_available():
        return api.search_flights(origin, destination, date, seat_class)
    return []
