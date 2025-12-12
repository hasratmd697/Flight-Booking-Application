"""
Dynamic Pricing Feature Test Script
====================================
This script demonstrates the dynamic pricing algorithm by:
1. Getting available seats and their initial prices
2. Reserving seats progressively
3. Showing how prices increase as occupancy goes up

Usage: python test_dynamic_pricing.py
"""

import requests
import time

BASE_URL = "https://flight-app-2025.el.r.appspot.com"

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
    # Try flight IDs from 1 to 20000 (checking in batches)
    for flight_id in range(1, 20000, 100):
        for fid in range(flight_id, min(flight_id + 100, 20000)):
            try:
                data = get_available_seats(fid)
                if data.get('success'):
                    seats = data.get('seats', [])
                    available = [s for s in seats if s['status'] == 'available']
                    if len(available) >= 10:  # Need at least 10 seats for good demo
                        print(f"   ✅ Found flight ID {fid} with {len(available)} available seats")
                        return fid, data
            except:
                pass
        print(f"   Checked flights {flight_id}-{flight_id+99}...")
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
    print("DYNAMIC PRICING DEMONSTRATION")
    print("=" * 60)
    
    # Step 1: Find a flight with available seats
    print("\n📊 Step 1: Finding a flight with available seats...")
    flight_id, data = find_flight_with_seats()
    
    if not flight_id:
        print("❌ No flights with available seats found!")
        return
    
    seats = data.get('seats', [])
    available_seats = [s for s in seats if s['status'] == 'available']
    
    print(f"   Total seats: {len(seats)}")
    print(f"   Available seats: {len(available_seats)}")
    
    # Show initial price distribution
    print("\n💰 Initial Price Distribution:")
    prices = [s['price'] for s in available_seats[:10]]
    for i, seat in enumerate(available_seats[:5]):
        print(f"   Seat {seat['number']}: ₹{seat['price']}")
    
    initial_avg_price = sum(prices) / len(prices) if prices else 0
    print(f"\n   Average price (first 10 seats): ₹{initial_avg_price:.2f}")
    
    # Step 2: Reserve seats progressively and track price changes
    print("\n🎟️  Step 2: Reserving seats and tracking price changes...")
    reserved_seats = []
    price_history = []
    
    # Reserve seats in batches
    batches = [5, 10, 15, 20]
    
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
            if updated_seats:
                current_prices = [s['price'] for s in updated_seats[:10]]
                avg_price = sum(current_prices) / len(current_prices)
                occupancy = (len(seats) - len(updated_seats)) / len(seats) * 100
                
                price_history.append({
                    'reserved': len(reserved_seats),
                    'occupancy': occupancy,
                    'avg_price': avg_price
                })
                
                print(f"\n   After reserving {len(reserved_seats)} seats:")
                print(f"   📈 Occupancy: {occupancy:.1f}%")
                print(f"   💵 New average price: ₹{avg_price:.2f}")
                if initial_avg_price > 0:
                    increase = ((avg_price - initial_avg_price) / initial_avg_price) * 100
                    print(f"   📊 Price increase: {increase:.1f}%")
        
        time.sleep(0.5)  # Small delay between batches
    
    # Step 3: Summary
    print("\n" + "=" * 60)
    print("📋 DYNAMIC PRICING SUMMARY")
    print("=" * 60)
    
    print("\n   Seats Reserved | Occupancy | Avg Price | Price Increase")
    print("   " + "-" * 55)
    
    for record in price_history:
        increase = ((record['avg_price'] - initial_avg_price) / initial_avg_price * 100) if initial_avg_price > 0 else 0
        print(f"   {record['reserved']:^14} | {record['occupancy']:^9.1f}% | ₹{record['avg_price']:^8.2f} | {increase:^13.1f}%")
    
    # Step 4: Clean up - release all reserved seats
    print("\n🧹 Step 3: Cleaning up (releasing all reserved seats)...")
    for seat in reserved_seats:
        release_seat(seat['id'])
    print(f"   Released {len(reserved_seats)} seats")
    
    print("\n✅ Dynamic pricing demonstration complete!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_dynamic_pricing()
