"""
Concurrency Feature Test Script
===============================
This script demonstrates the concurrency handling by:
1. Sending multiple simultaneous requests to reserve the same seat
2. Verifying that only one reservation succeeds
3. Testing race condition handling

Usage: python test_concurrency.py
"""

import requests
import concurrent.futures
import time
from threading import Lock

BASE_URL = "https://flight-app-2025.el.r.appspot.com"

# Thread-safe counters
results_lock = Lock()
success_count = 0
failure_count = 0
results = []

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
                    if len(available) >= 1:
                        print(f"   ✅ Found flight ID {fid} with {len(available)} available seats")
                        return fid, data
            except:
                pass
        print(f"   Checked flights {flight_id}-{flight_id+99}...")
    return None, None

def reserve_seat(seat_id, thread_id):
    """Reserve a specific seat and track results"""
    global success_count, failure_count, results
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/seats/reserve",
            json={"seat_id": seat_id},
            timeout=30
        )
        elapsed = time.time() - start_time
        result = response.json()
        
        with results_lock:
            if result.get('success'):
                success_count += 1
                status = "✅ SUCCESS"
            else:
                failure_count += 1
                status = "❌ FAILED"
            
            results.append({
                'thread_id': thread_id,
                'success': result.get('success', False),
                'message': result.get('error', 'Reserved'),
                'elapsed': elapsed
            })
        
        return result
    except Exception as e:
        with results_lock:
            failure_count += 1
            results.append({
                'thread_id': thread_id,
                'success': False,
                'message': str(e),
                'elapsed': time.time() - start_time
            })
        return {'success': False, 'error': str(e)}

def release_seat(seat_id):
    """Release a reserved seat"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/seats/release",
            json={"seat_id": seat_id}
        )
        return response.json()
    except:
        return {'success': False}

def test_concurrent_reservations(seat_id, num_threads=5):
    """Test concurrent reservation attempts on the same seat"""
    global success_count, failure_count, results
    success_count = 0
    failure_count = 0
    results = []
    
    print(f"\n🔄 Sending {num_threads} concurrent requests to reserve seat ID: {seat_id}")
    print("-" * 50)
    
    # Use ThreadPoolExecutor for concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks at once
        futures = [
            executor.submit(reserve_seat, seat_id, i+1) 
            for i in range(num_threads)
        ]
        
        # Wait for all to complete
        concurrent.futures.wait(futures)
    
    # Print results
    print("\n📊 Results:")
    print("-" * 50)
    
    for r in sorted(results, key=lambda x: x['thread_id']):
        status = "✅ SUCCESS" if r['success'] else "❌ BLOCKED"
        print(f"   Thread {r['thread_id']}: {status} ({r['elapsed']:.3f}s) - {r['message']}")
    
    return success_count, failure_count

def demonstrate_concurrency():
    print("=" * 60)
    print("CONCURRENCY FEATURE DEMONSTRATION")
    print("=" * 60)
    
    # Step 1: Find a flight with available seats
    print("\n📊 Step 1: Finding an available seat for testing...")
    flight_id, data = find_flight_with_seats()
    
    if not flight_id:
        print("❌ No flights with available seats found!")
        return
    
    seats = data.get('seats', [])
    available_seats = [s for s in seats if s['status'] == 'available']
    
    test_seat = available_seats[0]
    print(f"   Using seat: {test_seat['number']} (ID: {test_seat['id']})")
    
    # Step 2: Test concurrent reservations
    print("\n🧪 Step 2: Testing concurrent reservations...")
    print("   Sending 5 simultaneous requests to reserve the SAME seat")
    
    successes, failures = test_concurrent_reservations(test_seat['id'], num_threads=5)
    
    # Step 3: Verify results
    print("\n" + "=" * 60)
    print("📋 CONCURRENCY TEST RESULTS")
    print("=" * 60)
    
    print(f"\n   ✅ Successful reservations: {successes}")
    print(f"   ❌ Blocked/Failed requests: {failures}")
    
    if successes == 1 and failures == 4:
        print("\n   🎉 PERFECT! Only 1 request succeeded (as expected)")
        print("   ✅ Concurrency handling is working correctly!")
    elif successes == 0:
        print("\n   ⚠️  No reservations succeeded - seat might already be reserved")
    elif successes > 1:
        print("\n   ⚠️  WARNING: Multiple reservations succeeded!")
        print("   ❌ This indicates a potential race condition issue")
    else:
        print(f"\n   ℹ️  {successes} succeeded, {failures} failed")
    
    # Step 4: Clean up
    print("\n🧹 Step 3: Cleaning up (releasing the test seat)...")
    release_result = release_seat(test_seat['id'])
    if release_result.get('success'):
        print("   ✅ Seat released successfully")
    else:
        print(f"   ⚠️  Could not release seat: {release_result.get('error', 'Unknown')}")
    
    # Step 5: Additional test - Sequential bookings
    print("\n" + "=" * 60)
    print("🧪 BONUS TEST: Sequential Double-Booking Attempt")
    print("=" * 60)
    
    # Reserve the seat
    print("\n   1️⃣  First reservation attempt...")
    result1 = requests.post(
        f"{BASE_URL}/api/seats/reserve",
        json={"seat_id": test_seat['id']}
    ).json()
    print(f"      Result: {'✅ SUCCESS' if result1.get('success') else '❌ FAILED'}")
    
    # Try to reserve the same seat again
    print("\n   2️⃣  Second reservation attempt (same seat)...")
    result2 = requests.post(
        f"{BASE_URL}/api/seats/reserve",
        json={"seat_id": test_seat['id']}
    ).json()
    print(f"      Result: {'✅ SUCCESS' if result2.get('success') else '❌ BLOCKED'}")
    
    if result1.get('success') and not result2.get('success'):
        print("\n   🎉 CORRECT! Second booking was properly blocked")
    
    # Clean up
    release_seat(test_seat['id'])
    
    print("\n" + "=" * 60)
    print("✅ Concurrency demonstration complete!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_concurrency()
