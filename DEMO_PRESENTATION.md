# 🎯 Flight Booking Application - Demo Presentation Guide

> **Prepared by:** Hasrat Hussain  
> **Project Type:** Infosys Internship Capstone Project  
> **Live Demo:** [https://flight-app-2025.el.r.appspot.com](https://flight-app-2025.el.r.appspot.com)

---

## 📋 Executive Summary

This is a **full-stack flight booking application** built using **Django (Python)** and deployed on **Google Cloud Platform**. It simulates real airline booking systems with features like dynamic pricing, real-time seat selection, and secure payment processing.

| Key Metric               | Value                                                  |
| ------------------------ | ------------------------------------------------------ |
| **Lines of Code**        | ~5,000+                                                |
| **Database Models**      | 7 (User, Place, Week, Flight, Seat, Passenger, Ticket) |
| **Test Cases**           | 50+ comprehensive tests                                |
| **API Endpoints**        | 15+                                                    |
| **Airlines Covered**     | Multiple (domestic & international)                    |
| **Airports in Database** | 100+ worldwide                                         |

---

## 🛠️ Technology Stack

### Backend

| Technology     | Version | Purpose                          |
| -------------- | ------- | -------------------------------- |
| **Python**     | 3.11+   | Core programming language        |
| **Django**     | 3.1.2   | Web framework (MTV architecture) |
| **Gunicorn**   | 20.1.0  | WSGI HTTP Server                 |
| **WhiteNoise** | 6.2.0   | Static file serving              |

### Database

| Technology          | Purpose                       |
| ------------------- | ----------------------------- |
| **SQLite**          | Local development             |
| **PostgreSQL 14**   | Production (Google Cloud SQL) |
| **psycopg2-binary** | PostgreSQL adapter for Python |

### Frontend

| Technology     | Purpose                     |
| -------------- | --------------------------- |
| **HTML5**      | Page structure              |
| **CSS3**       | Styling (Crimson theme)     |
| **JavaScript** | Interactive features (AJAX) |
| **Bootstrap**  | Responsive design framework |

### Deployment

| Service               | Purpose                                    |
| --------------------- | ------------------------------------------ |
| **Google App Engine** | Application hosting (Standard Environment) |
| **Google Cloud SQL**  | Managed PostgreSQL database                |
| **Region**            | asia-south1 (Mumbai)                       |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  HTML    │  │   CSS    │  │    JS    │  │Bootstrap │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┴──────────────┴──────────────┴──────────────┴────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DJANGO FRAMEWORK                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    URL Routing (urls.py)                  │  │
│  └────────────────────────────┬─────────────────────────────┘  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Views (views.py)                       │  │
│  │  • Authentication (login, register, logout)               │  │
│  │  • Flight Search & Results                                │  │
│  │  • Seat Selection                                         │  │
│  │  • Booking & Payment                                      │  │
│  │  • Ticket Management                                      │  │
│  └────────────────────────────┬─────────────────────────────┘  │
│                               ▼                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ Dynamic Pricing │  │  Seat Manager   │  │    Models      │  │
│  │ (Algorithm)     │  │  (Concurrency)  │  │   (ORM)        │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
└───────────┴─────────────────────┴─────────────────────┴─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│           ┌────────────────────────────────────┐                │
│           │  PostgreSQL (Cloud SQL)            │                │
│           │  • flightdb database               │                │
│           │  • Connection via Unix socket      │                │
│           └────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure Explained

```
Flight-Booking-Application/
│
├── capstone/                    # Django Project Configuration
│   ├── settings.py              # Database, middleware, installed apps
│   ├── urls.py                  # Root URL configuration
│   └── wsgi.py                  # WSGI entry point
│
├── flight/                      # Main Application
│   ├── models.py                # 7 database models
│   ├── views.py                 # 28 view functions (~917 lines)
│   ├── urls.py                  # 18 URL patterns
│   ├── dynamic_pricing.py       # 💰 Pricing algorithm
│   ├── seat_manager.py          # 🪑 Seat reservation logic
│   ├── utils.py                 # Data loading utilities
│   ├── tests.py                 # ✅ 50+ test cases
│   ├── templates/               # 17 HTML templates
│   └── static/                  # CSS, JavaScript, images
│
├── Data/                        # Pre-loaded flight data
│   ├── airports.csv             # Airport information
│   ├── domestic_flights.csv     # ~473KB of flight data
│   └── international_flights.csv # ~623KB of flight data
│
├── app.yaml                     # Google App Engine config
├── requirements.txt             # Python dependencies
└── manage.py                    # Django management script
```

---

## 📊 Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ • id (PK)       │
│ • username      │
│ • email         │
│ • password      │──────────┐
│ • first_name    │          │
│ • last_name     │          │
└─────────────────┘          │
                             │
┌─────────────────┐          │ owns
│     Place       │          │
├─────────────────┤          │
│ • id (PK)       │          │
│ • city          │◀─────┐   │
│ • airport       │      │   │
│ • code (3 char) │      │   │
│ • country       │      │   │
└─────────────────┘      │   │
                         │   │
┌─────────────────┐      │   │      ┌─────────────────┐
│     Week        │      │   │      │     Ticket      │
├─────────────────┤      │   │      ├─────────────────┤
│ • id (PK)       │      │   └──────│ • user (FK)     │
│ • number (0-6)  │      │          │ • ref_no (6chr) │
│ • name          │      │   ┌──────│ • flight (FK)   │
└────────┬────────┘      │   │      │ • flight_ddate  │
         │ M2M           │   │      │ • seat_class    │
         ▼               │   │      │ • total_fare    │
┌─────────────────┐      │   │      │ • status        │
│     Flight      │──────┴───┘      │ • passengers    │──┐
├─────────────────┤                 └────────┬────────┘  │
│ • id (PK)       │                          │ M2M       │
│ • origin (FK)   │                          ▼           │
│ • destination   │                 ┌─────────────────┐  │
│ • depart_time   │                 │      Seat       │  │
│ • depart_day    │                 ├─────────────────┤  │
│ • duration      │                 │ • flight (FK)   │  │
│ • arrival_time  │◀────────────────│ • seat_number   │  │
│ • plane         │                 │ • seat_class    │  │
│ • airline       │                 │ • status        │  │
│ • economy_fare  │                 │ • price         │  │
│ • business_fare │                 │ • reserved_until│  │
│ • first_fare    │                 └─────────────────┘  │
└─────────────────┘                                      │
                                    ┌─────────────────┐  │
                                    │   Passenger     │◀─┘
                                    ├─────────────────┤
                                    │ • first_name    │
                                    │ • last_name     │
                                    │ • gender        │
                                    └─────────────────┘
```

### Model Details

| Model         | Fields                             | Key Features                               |
| ------------- | ---------------------------------- | ------------------------------------------ |
| **User**      | username, email, password, names   | Custom user extending AbstractUser         |
| **Place**     | city, airport, code, country       | 3-character IATA codes (JFK, LAX, etc.)    |
| **Week**      | number (0-6), name                 | Maps to flight schedules                   |
| **Flight**    | origin, destination, times, fares  | Many-to-many with Week days                |
| **Seat**      | flight, seat_number, class, status | Unique constraint on (flight, seat_number) |
| **Passenger** | first_name, last_name, gender      | Linked to tickets                          |
| **Ticket**    | ref_no, user, flight, fare, status | 6-character unique booking reference       |

---

## ✨ Key Features Deep Dive

### 1. 🔍 Flight Search System

**How it works:**

1. User enters origin, destination, date, and seat class
2. System converts date to weekday (0=Monday, 6=Sunday)
3. Filters flights that operate on that day
4. Applies dynamic pricing based on demand
5. Returns sorted results

**Code Location:** `flight/views.py` - `flight()` function (Lines 156-295)

**API Endpoint:**

```
GET /flight?Origin=DEL&Destination=BOM&DepartDate=2025-12-15&SeatClass=economy&TripType=1
```

---

### 2. 💰 Dynamic Pricing Algorithm

> **Location:** `flight/dynamic_pricing.py`

This is a **key differentiator** - simulating real airline pricing!

#### Price Calculation Formula:

```
Final Price = Base Price × Occupancy Multiplier × Time Multiplier
```

#### Occupancy-Based Pricing:

| Occupancy Rate | Multiplier | Description                      |
| -------------- | ---------- | -------------------------------- |
| < 30%          | 0.85x      | 📉 Low demand discount (15% off) |
| 30-50%         | 1.00x      | 📊 Normal base price             |
| 50-70%         | 1.15x      | 📈 Moderate demand (+15%)        |
| 70-85%         | 1.30x      | 🔥 High demand (+30%)            |
| > 85%          | 1.50x      | 🚀 Surge pricing (+50%)          |

#### Time-Based Pricing:

| Days to Departure | Multiplier | Description                      |
| ----------------- | ---------- | -------------------------------- |
| > 30 days         | 0.90x      | ✈️ Early bird discount (10% off) |
| 15-30 days        | 1.00x      | Normal price                     |
| 7-14 days         | 1.10x      | Moderate urgency (+10%)          |
| 3-6 days          | 1.20x      | Last week premium (+20%)         |
| < 3 days          | 1.30x      | 🔥 Last minute surge (+30%)      |

**Example Calculation:**

```
Base Economy Fare: ₹5,000
Occupancy: 60% → Multiplier: 1.15
Days to Departure: 5 → Multiplier: 1.20

Final Price = ₹5,000 × 1.15 × 1.20 = ₹6,900
```

---

### 3. 🪑 Interactive Seat Selection

> **Location:** `flight/seat_manager.py`

#### Seat Configuration (Boeing 737 Layout):

```
First Class:    Rows 1-3   × 2 seats (A, F)         =   6 seats
Business Class: Rows 4-8   × 4 seats (A, C, D, F)   =  20 seats
Economy Class:  Rows 9-33  × 6 seats (A-F)          = 150 seats
                                         TOTAL:       176 seats
```

#### Concurrency Control:

- Uses **database-level row locking** (`select_for_update()`)
- **10-minute temporary reservation** window
- Automatic cleanup of expired reservations

#### Seat States:

| Status    | Color     | Description               |
| --------- | --------- | ------------------------- |
| Available | 🟢 Green  | Can be selected           |
| Reserved  | 🟡 Yellow | Temporarily held (10 min) |
| Booked    | 🔴 Red    | Confirmed booking         |

**API Endpoints:**

```
GET  /api/seats/available?flight_id=1&seat_class=economy
POST /api/seats/reserve   {seat_id: 123}
POST /api/seats/release   {seat_id: 123}
POST /api/seats/confirm   {seat_ids: [123, 124]}
```

---

### 4. 💳 Secure Payment System

**Validation Implemented:**

- ✅ 16-digit card number (Luhn algorithm ready)
- ✅ Card holder name validation
- ✅ Expiry date validation (not in past)
- ✅ 3-digit CVV validation
- ✅ Server-side double validation

> **Note:** This is a simulated payment system (no real transactions)

---

### 5. 👤 User Authentication

**Features:**

- User registration with password confirmation
- Login/Logout functionality
- Session management via Django sessions
- Protected booking routes

**URL Patterns:**

```
/login    → Login page
/register → Registration page
/logout   → Logout action
```

---

## 🔐 Security Features

| Feature                      | Implementation                      |
| ---------------------------- | ----------------------------------- |
| **CSRF Protection**          | Django's built-in CSRF middleware   |
| **SQL Injection Prevention** | Django ORM parameterized queries    |
| **Password Hashing**         | Django's PBKDF2 algorithm           |
| **Input Validation**         | Both client-side and server-side    |
| **Environment Variables**    | Sensitive data in environment       |
| **HTTPS Only**               | Enforced in production (App Engine) |

---

## ☁️ Deployment Architecture

```
                                    ┌─────────────────────────┐
                                    │   Google Cloud Platform  │
                                    └──────────┬──────────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
              ▼                                ▼                                ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│   App Engine         │      │     Cloud SQL        │      │   Static Files       │
│   (Standard Env)     │─────▶│   (PostgreSQL 14)    │      │   (WhiteNoise)       │
├──────────────────────┤      ├──────────────────────┤      ├──────────────────────┤
│ • Python 3.11        │      │ • Instance: db-f1-micro│     │ • CSS, JS, Images   │
│ • Instance: F2       │      │ • Database: flightdb │      │ • Served via CDN    │
│ • Auto-scaling 1-2   │      │ • Unix socket conn   │      │                      │
│ • Gunicorn WSGI      │      │ • 10GB storage       │      │                      │
└──────────────────────┘      └──────────────────────┘      └──────────────────────┘
```

### Deployment Commands:

```bash
# Set project
gcloud config set project flight-app-2025

# Deploy
gcloud app deploy app.yaml --quiet

# View logs
gcloud app logs tail -s default

# Open app
gcloud app browse
```

---

## 🧪 Testing Strategy

**Test Coverage:** 50+ test cases across multiple test classes

| Test Class               | Purpose                   | Tests    |
| ------------------------ | ------------------------- | -------- |
| `ModelTestCase`          | Database model validation | 7 tests  |
| `AuthenticationTestCase` | Login/Register/Logout     | 8 tests  |
| `IndexViewTestCase`      | Home page functionality   | 4 tests  |
| `FlightSearchTestCase`   | Search functionality      | 5 tests  |
| `PlaceQueryTestCase`     | Autocomplete API          | 3 tests  |
| `SeatManagerTestCase`    | Seat operations           | 10 tests |
| `SeatAPITestCase`        | API endpoints             | 6 tests  |
| `BookingFlowTestCase`    | End-to-end booking        | 7+ tests |

**Run Tests:**

```bash
# All tests
python manage.py test

# Specific app
python manage.py test flight

# With verbosity
python manage.py test flight --verbosity=2
```

---

## 🎮 Demo Flow Script

Follow this sequence for your demo:

### Part 1: User Registration & Login (2 mins)

1. Navigate to homepage: `http://127.0.0.1:8000`
2. Click "Register" → Create account
3. Login with credentials
4. Show user is now logged in (name in navbar)

### Part 2: Flight Search (3 mins)

1. Enter search criteria:
   - Origin: `DEL` (Delhi)
   - Destination: `BOM` (Mumbai)
   - Date: Pick a future date
   - Class: Economy
   - Trip Type: One-way
2. Click Search
3. **Point out:** Dynamic pricing indicators, flight duration, airline logos

### Part 3: Seat Selection (3 mins)

1. Select a flight → Redirected to seat selection
2. **Point out:**
   - Color-coded seat map
   - First/Business/Economy sections
   - Available vs Booked seats
3. Click on available seat → Changes to "selected"
4. Show that selecting another seat updates total

### Part 4: Booking & Payment (3 mins)

1. Enter passenger details
2. Proceed to payment
3. Enter (sample) card details:
   - Card: 4111 1111 1111 1111
   - Expiry: 12/26
   - CVV: 123
4. Complete booking
5. Show confirmation screen with booking reference

### Part 5: Ticket Management (2 mins)

1. Go to "My Bookings"
2. Show ticket details
3. Demonstrate cancel ticket option

### Part 6: Technical Highlights (3 mins)

1. Open browser DevTools → Network tab
2. Show AJAX calls for:
   - Airport autocomplete
   - Dynamic pricing API
   - Seat availability updates
3. Show responsive design (resize window)

---

## 💡 Talking Points for Q&A

### "Why Django?"

> Django provides a complete MVC framework with built-in ORM, authentication, admin interface, and security features. It's battle-tested and follows "batteries included" philosophy - perfect for rapid development.

### "How does dynamic pricing work?"

> We simulate real airline pricing with a two-factor model: occupancy rate and time to departure. Higher demand = higher prices. Last-minute bookings cost more. This creates realistic pricing behavior.

### "How do you handle concurrent seat bookings?"

> We use database-level row locking with `select_for_update()` and a 10-minute temporary reservation system. If two users try the same seat, only the first gets it - the second sees "Already Reserved."

### "Why Google Cloud Platform?"

> GCP offers managed services like App Engine and Cloud SQL that handle auto-scaling, SSL, and database management. It's cost-effective for demo apps and scales to production easily.

### "What would you add next?"

> Email notifications for bookings, real payment gateway integration (Razorpay/Stripe), PDF ticket generation, and possibly a mobile app using React Native.

---

## 📈 Project Statistics

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CODE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
views.py        │  917 lines  │ View controllers
models.py       │  126 lines  │ Database models
tests.py        │ 1212 lines  │ Test suite
dynamic_pricing │  224 lines  │ Pricing algorithm
seat_manager    │  224 lines  │ Seat operations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEMPLATES       │   17 files  │ HTML templates
DATA FILES      │ ~1.1 MB     │ Flight data (CSV)
DATABASE        │ ~2.9 MB     │ SQLite (local)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚀 Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/hasratmd697/Flight-Booking-Application.git
cd Flight-Booking-Application

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load initial data
python manage.py shell -c "from flight.utils import createWeekDays, addPlaces, addDomesticFlights; createWeekDays(); addPlaces(); addDomesticFlights()"

# Start server
python manage.py runserver

# Run tests
python manage.py test flight
```

---

## 📱 Live Demo URLs

| Environment    | URL                                                                                  |
| -------------- | ------------------------------------------------------------------------------------ |
| **Production** | [https://flight-app-2025.el.r.appspot.com](https://flight-app-2025.el.r.appspot.com) |
| **Local**      | [http://127.0.0.1:8000](http://127.0.0.1:8000)                                       |

---

<p align="center">
  <img src="https://img.shields.io/badge/Made_with-Django-green?style=for-the-badge&logo=django" alt="Django"/>
  <img src="https://img.shields.io/badge/Deployed_on-Google_Cloud-blue?style=for-the-badge&logo=google-cloud" alt="GCP"/>
  <img src="https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge" alt="Status"/>
</p>

<p align="center">
  <strong>Made with ❤️ by Hasrat Hussain | Infosys Internship Project 2025</strong>
</p>
