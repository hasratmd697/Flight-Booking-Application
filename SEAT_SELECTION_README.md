# Seat Selection Feature - Documentation

## Overview

A complete seat selection system has been added to your Flight booking application with:

- **Interactive UI** - Beautiful airplane seat map visualization
- **Concurrency Control** - Database-level row locking prevents double-booking
- **Real-time Updates** - AJAX-based seat reservation system
- **Automatic Cleanup** - Expired seat reservations are automatically released

## Features Implemented

### 1. Backend (Django)

#### New Models (`flight/models.py`)

- **Seat Model**: Stores individual seats with status tracking
  - `flight`: Foreign key to Flight
  - `seat_number`: Seat identifier (e.g., '1A', '2B')
  - `seat_class`: economy/business/first
  - `status`: available/booked/reserved
  - `price`: Seat-specific pricing
  - `reserved_until`: Temporary hold timestamp

#### Concurrency Control (`flight/seat_manager.py`)

- **Row-level locking**: Uses Django's `select_for_update()` to prevent race conditions
- **Transaction management**: Atomic operations ensure data consistency
- **Automatic expiration**: Cleans up reservations after 10 minutes

Key Functions:

- `create_seats_for_flight(flight)` - Generate seat layout for a flight
- `reserve_seat(seat_id)` - Temporarily hold a seat
- `book_seat(seat_id)` - Confirm seat booking
- `release_seat(seat_id)` - Free up a reserved seat
- `cleanup_expired_reservations()` - Remove stale reservations

#### API Endpoints (`flight/views.py` & `flight/urls.py`)

- `GET /flight/seats` - Seat selection page
- `GET /api/seats/available` - Get seat availability (AJAX)
- `POST /api/seats/reserve` - Reserve seat temporarily (AJAX)
- `POST /api/seats/release` - Release reserved seat (AJAX)
- `POST /api/seats/confirm` - Confirm seat booking (AJAX)

### 2. Frontend

#### Seat Selection UI (`templates/flight/seat_selection.html`)

Beautiful, modern interface featuring:

- **Airplane visualization** with cockpit and cabin
- **Color-coded seats**:
  - 🟢 Green = Available
  - 🔵 Blue = Selected (by user)
  - 🟣 Purple = Reserved (by others)
  - ⚪ Grey = Booked
- **Real-time price calculation**
- **Interactive seat map** with click-to-select
- **Responsive design** for mobile and desktop
- **Loading states** and notifications

Design Elements:

- Gradient backgrounds
- Smooth animations
- Modern typography (Google Fonts - Inter)
- Glassmorphism effects
- Premium color palette

### 3. Concurrency Features

#### How Race Conditions are Prevented:

1. **Database Transactions**: All seat operations wrapped in `@transaction.atomic`
2. **Row-Level Locking**: `select_for_update()` locks seat rows during updates
3. **Temporary Reservations**: 10-minute holds prevent conflicts
4. **Status Checks**: Validates seat availability before every operation
5. **Automatic Cleanup**: Background process releases expired holds

Example Scenario:

```
User A clicks seat 1A → Server locks row → Sets to 'reserved' → Saves
User B clicks seat 1A → Server sees 'reserved' → Returns error → User B sees "already reserved"
```

## Setup Instructions

### 1. Database Migration

The migrations have already been created and applied. If you need to rerun:

```bash
python main.py makemigrations
python main.py migrate
```

### 2. Initialize Seats for Existing Flights

Run this script to create seats for all flights:

```bash
python main.py shell < create_all_seats.py
```

Or manually in Django shell:

```python
from flight.models import Flight
from flight.seat_manager import create_seats_for_flight

for flight in Flight.objects.all():
    if not flight.seats.exists():
        create_seats_for_flight(flight)
```

### 3. Access Seat Selection

#### Method 1: Direct URL

Navigate to:

```
http://localhost:8000/flight/seats?flight_id=1&seat_class=economy&depart_date=2025-12-05
```

Parameters:

- `flight_id`: ID of the flight
- `seat_class`: economy/business/first
- `depart_date`: Departure date (YYYY-MM-DD)

#### Method 2: Integration with Booking Flow

After selecting a flight, users can click "Select Seats" to access the seat map.

## Seat Layout Configuration

### Economy Class (Rows 1-25)

- 6 seats per row (A, B, C, D, E, F)
- 150 total seats
- Standard pricing

### Business Class (Rows 26-30)

- 4 seats per row (A, B, C, D)
- 20 total seats
- Premium pricing

### First Class (Rows 31-33)

- 2 seats per row (A, B)
- 6 total seats
- Luxury pricing

Total seats per aircraft: **176 seats** (if all classes available)

## API Usage Examples

### Get Available Seats

```javascript
fetch("/api/seats/available?flight_id=1&seat_class=economy")
  .then((res) => res.json())
  .then((data) => console.log(data.seats));
```

### Reserve a Seat

```javascript
fetch("/api/seats/reserve", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ seat_id: 42 }),
})
  .then((res) => res.json())
  .then((data) => {
    if (data.success) {
      console.log("Reserved until:", data.reserved_until);
    }
  });
```

### Confirm Booking

```javascript
fetch("/api/seats/confirm", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    seat_ids: [42, 43],
    flight_id: 1,
  }),
})
  .then((res) => res.json())
  .then((data) => {
    if (data.success) {
      console.log("Seats booked!");
    }
  });
```

## Testing the Concurrency Feature

### Test 1: Basic Concurrency

1. Open the seat selection page in two different browsers (Chrome & Firefox)
2. Try to click the same seat in both browsers simultaneously
3. One will succeed, the other will show "Seat already reserved"

### Test 2: Reservation Timeout

1. Select a seat and wait 10 minutes
2. The reservation will automatically expire
3. Refresh the page - seat becomes available again

### Test 3: Transaction Rollback

1. Select multiple seats
2. If one fails to book, all selected seats are released
3. Ensures all-or-nothing booking

## Customization Options

### Change Reservation Duration

In `flight/seat_manager.py`:

```python
def reserve_seat(seat_id, duration_minutes=10):  # Change this value
```

### Modify Seat Layout

In `flight/seat_manager.py`, edit the `create_seats_for_flight()` function:

```python
# Change economy class configuration
economy_rows = range(1, 26)  # Modify range
economy_columns = ['A', 'B', 'C', 'D', 'E', 'F']  # Modify columns
```

### Customize UI Colors

In `templates/flight/seat_selection.html`, modify CSS:

```css
.seat.available {
  background: linear-gradient(180deg, #10b981 0%, #059669 100%); /* Green */
}
.seat.selected {
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%); /* Blue */
}
```

## Database Schema

### Seat Table Structure

```sql
CREATE TABLE flight_seat (
    id INTEGER PRIMARY KEY,
    flight_id INTEGER REFERENCES flight_flight(id),
    seat_number VARCHAR(5),
    seat_class VARCHAR(20),
    status VARCHAR(20) DEFAULT 'available',
    price FLOAT,
    reserved_until TIMESTAMP NULL,
    UNIQUE (flight_id, seat_number)
);

CREATE INDEX idx_flight_status ON flight_seat(flight_id, status);
```

### Ticket-Seat Relationship

Many-to-Many through `ticket_selected_seats` table:

```sql
CREATE TABLE ticket_selected_seats (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER REFERENCES flight_ticket(id),
    seat_id INTEGER REFERENCES flight_seat(id)
);
```

## Admin Panel

Seats can be managed through Django admin at `/admin`:

- View all seats for a flight
- Manually change seat status
- Monitor reservations
- Bulk actions

## Performance Considerations

### Database Indexes

- Index on `(flight, status)` for fast availability queries
- Unique constraint on `(flight, seat_number)` prevents duplicates

### Caching Strategies (Future Enhancement)

```python
# Cache seat availability for 30 seconds
from django.core.cache import cache

def get_cached_seats(flight_id):
    cache_key = f'seats_flight_{flight_id}'
    seats = cache.get(cache_key)
    if not seats:
        seats = Seat.objects.filter(flight_id=flight_id)
        cache.set(cache_key, seats, 30)  # 30 seconds
    return seats
```

### Auto-refresh

The UI automatically refreshes seat availability every 30 seconds to show real-time updates.

## Troubleshooting

### Issue: Seats not showing

**Solution**: Run `create_seats_for_flight(flight)` for that flight

### Issue: "Seat already reserved" error

**Solution**: Wait for reservation to expire (10 min) or manually release in admin

### Issue: Race condition still occurring

**Solution**: Ensure database supports row-level locking (SQLite 3.7.11+, PostgreSQL, MySQL)

### Issue: Performance slow with many seats

**Solution**: Add pagination or implement caching layer

## Future Enhancements

1. **Seat Preferences**: Allow users to save favorite seats
2. **Dynamic Pricing**: Adjust prices based on seat popularity
3. **Group Booking**: Auto-select adjacent seats for groups
4. **Seat Swap**: Allow passengers to exchange seats
5. **Real-time WebSocket**: Push updates without polling
6. **Accessibility Features**: Wheelchair accessible seats, etc.

## Security Notes

- CSRF protection enabled on all POST endpoints
- User authentication required for booking
- Input validation on all seat operations
- SQL injection prevented by Django ORM
- XSS protection through template escaping

## License & Credits

- Built for Flight Booking System
- Uses Django 3.1.2
- Concurrency control via PostgreSQL/SQLite row locking
- UI inspired by modern airline booking systems

---

**Need Help?** Check the inline code comments or Django documentation for more details.
