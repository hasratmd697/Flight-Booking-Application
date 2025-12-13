"""
Dynamic Pricing Feature Test Script (LOCAL VERSION)
====================================================
This script tests the dynamic pricing algorithm LOCALLY to verify
that prices inflate as seat occupancy increases.

Usage: 
1. Start local server: python manage.py runserver
2. Run this test: python test_dynamic_pricing_local.py
"""

import requests
import time

# Use LOCAL server for testing
BASE_URL = "http://127.0.0.1:8000"

def get_available_seats(flight_id, seat_class="economy"):
    """Fetch available seats for a flight"""
    response = requests.get(
        f"{BASE_URL}/api/seats/available",
        params={"flight_id": flight_id, "seat_class": seat_class}
    )
    return response.json()

def find_flight_with_seats():
    """Find a flight ID that has available seats"""
    print("   Searching for a flight with available seats...")
    # Try flight IDs from 1 to 100 (smaller range for local testing)
    for flight_id in range(1, 100):
        try:
            data = get_available_seats(flight_id)
            if data.get('success'):
                seats = data.get('seats', [])
                available = [s for s in seats if s['status'] == 'available']
                if len(available) >= 10:  # Need at least 10 seats for good demo
                    print(f"   ✅ Found flight ID {flight_id} with {len(available)} available seats")
                    return flight_id, data
        except Exception as e:
            pass
    return None, None

def reserve_seat(seat_id):
    """Reserve a specific seat"""
    response = requests.post(
        f"{BASE_URL}/api/seats/reserve",
        json={"seat_id": seat_id}
    )
    return response.json()

def release_seat(seat_id):
    """Release a reserved seat"""
    response = requests.post(
        f"{BASE_URL}/api/seats/release",
        json={"seat_id": seat_id}
    )
    return response.json()

def demonstrate_dynamic_pricing():
    print("=" * 60)
    print("DYNAMIC PRICING DEMONSTRATION (LOCAL TEST)")
    print("=" * 60)
    
    # Step 1: Find a flight with available seats
    print("\n📊 Step 1: Finding a flight with available seats...")
    flight_id, data = find_flight_with_seats()
    
    if not flight_id:
        print("❌ No flights with available seats found!")
        print("   Make sure the local server is running: python manage.py runserver")
        return
    
    seats = data.get('seats', [])
    available_seats = [s for s in seats if s['status'] == 'available']
    
    print(f"   Total seats: {len(seats)}")
    print(f"   Available seats: {len(available_seats)}")
    
    # Show pricing info if available
    pricing_info = data.get('pricing_info', {})
    if pricing_info:
        print(f"\n📈 Current Pricing Info:")
        print(f"   Occupancy Rate: {pricing_info.get('occupancy_rate', 0)}%")
        print(f"   Price Multiplier: {pricing_info.get('price_multiplier', 1.0)}x")
    
    # Show initial price distribution
    print("\n💰 Initial Price Distribution:")
    prices = [s['price'] for s in available_seats[:10]]
    for i, seat in enumerate(available_seats[:5]):
        print(f"   Seat {seat['number']}: ₹{seat['price']} (base: ₹{seat.get('base_price', 'N/A')})")
    
    initial_avg_price = sum(prices) / len(prices) if prices else 0
    print(f"\n   Average price (first 10 seats): ₹{initial_avg_price:.2f}")
    
    # Step 2: Reserve seats progressively and track price changes
    print("\n🎟️  Step 2: Reserving seats and tracking price changes...")
    reserved_seats = []
    price_history = []
    
    # Reserve seats in batches (adjusted for 150 total economy seats)
    # 150 * 0.3 = 45 seats for 30% threshold
    # 150 * 0.5 = 75 seats for 50% threshold
    # 150 * 0.7 = 105 seats for 70% threshold
    # 150 * 0.85 = 127 seats for 85% threshold
    batches = [20, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]
    
    for batch_target in batches:
        if batch_target > len(available_seats):
            break
            
        # Reserve seats until we reach the batch target
        while len(reserved_seats) < batch_target and len(reserved_seats) < len(available_seats):
            seat = available_seats[len(reserved_seats)]
            result = reserve_seat(seat['id'])
            
            if result.get('success'):
                reserved_seats.append(seat)
            else:
                print(f"   ⚠️  Could not reserve seat {seat['number']}: {result.get('error')}")
                break
        
        # Get updated prices
        updated_data = get_available_seats(flight_id)
        if updated_data.get('success'):
            updated_seats = [s for s in updated_data['seats'] if s['status'] == 'available']
            pricing_info = updated_data.get('pricing_info', {})
            
            if updated_seats:
                current_prices = [s['price'] for s in updated_seats[:10]]
                avg_price = sum(current_prices) / len(current_prices)
                occupancy = pricing_info.get('occupancy_rate', 0)
                multiplier = pricing_info.get('price_multiplier', 1.0)
                
                price_history.append({
                    'reserved': len(reserved_seats),
                    'occupancy': occupancy,
                    'avg_price': avg_price,
                    'multiplier': multiplier
                })
                
                print(f"\n   After reserving {len(reserved_seats)} seats:")
                print(f"   📈 Occupancy: {occupancy:.1f}%")
                print(f"   🔢 Price Multiplier: {multiplier}x")
                print(f"   💵 New average price: ₹{avg_price:.2f}")
                if initial_avg_price > 0:
                    increase = ((avg_price - initial_avg_price) / initial_avg_price) * 100
                    print(f"   📊 Price increase: {increase:.1f}%")
        
        time.sleep(0.3)  # Small delay between batches
    
    # Step 3: Summary
    print("\n" + "=" * 70)
    print("📋 DYNAMIC PRICING SUMMARY")
    print("=" * 70)
    
    print("\n   Seats Reserved | Occupancy | Multiplier | Avg Price  | Price Increase")
    print("   " + "-" * 65)
    
    for record in price_history:
        increase = ((record['avg_price'] - initial_avg_price) / initial_avg_price * 100) if initial_avg_price > 0 else 0
        print(f"   {record['reserved']:^14} | {record['occupancy']:^9.1f}% | {record['multiplier']:^10}x | ₹{record['avg_price']:^8.2f} | {increase:^13.1f}%")
    
    # Step 4: Clean up - release all reserved seats
    print("\n🧹 Step 3: Cleaning up (releasing all reserved seats)...")
    for seat in reserved_seats:
        release_seat(seat['id'])
    print(f"   Released {len(reserved_seats)} seats")
    
    print("\n✅ Dynamic pricing demonstration complete!")
    print("=" * 60)
    
    # Verify dynamic pricing worked
    if price_history:
        final_multiplier = price_history[-1]['multiplier']
        if final_multiplier > 1.0:
            print("\n🎉 SUCCESS: Dynamic pricing is working!")
            print(f"   Price multiplier increased to {final_multiplier}x at high occupancy")
        else:
            print("\n⚠️  WARNING: Prices did not increase despite high occupancy")
            print("   Please verify the dynamic_pricing integration in views.py")

if __name__ == "__main__":
    demonstrate_dynamic_pricing()
