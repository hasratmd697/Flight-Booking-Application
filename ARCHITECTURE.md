# Flight Booking Application - Architecture Overview

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Browser   │  │  HTML/CSS   │  │ JavaScript  │              │
│  │   (User)    │  │  Templates  │  │  (Dynamic)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DJANGO APPLICATION                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    views.py (Controllers)                 │   │
│  │  • index() - Home page                                    │   │
│  │  • flight() - Search flights via API                      │   │
│  │  • book() - Create booking                                │   │
│  │  • payment() - Process payment                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────┐  ┌───────┴───────┐  ┌─────────────────────┐  │
│  │ flight_api.py │  │ seat_manager  │  │ dynamic_pricing.py  │  │
│  │ (Amadeus API) │  │    .py        │  │ (Price Calculator)  │  │
│  └───────┬───────┘  └───────────────┘  └─────────────────────┘  │
└──────────┼──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────────────────────┐
│   AMADEUS FLIGHT    │     │         GOOGLE CLOUD SQL            │
│        API          │     │         (PostgreSQL)                │
│  (External Service) │     │  • Users, Tickets, Bookings, Seats  │
└─────────────────────┘     └─────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Flight-Booking-Application/
├── capstone/                 # Django Project Config
│   ├── settings.py           # Database, API keys, middleware
│   ├── urls.py               # URL routing
│   └── utils.py              # PDF ticket generation
│
├── flight/                   # Main Application
│   ├── models.py             # Data models (User, Flight, Ticket, Seat)
│   ├── views.py              # Request handlers (1150 lines)
│   ├── flight_api.py         # Amadeus API integration
│   ├── seat_manager.py       # Real-time seat management
│   ├── dynamic_pricing.py    # Demand-based pricing
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JS, images
│
├── Data/                     # Static data
│   └── airports.csv          # Airport codes for autocomplete
│
└── app.yaml                  # GCP App Engine config
```

---

## 🔄 Key Data Flows

### 1. Flight Search Flow

```
User Input → views.flight() → AmadeusFlightAPI.search_flights()
                                       │
                                       ▼
                              Amadeus API (External)
                                       │
                                       ▼
                              Parse Response → Template
```

### 2. Booking Flow

```
Select Flight → Seat Selection → Passenger Details → Payment → Confirmation
     │               │                  │               │
     ▼               ▼                  ▼               ▼
  Session       seat_manager       Ticket Model    Update Status
  Storage        (Reserve)          (Create)       (CONFIRMED)
```

---

## 🧩 Core Components

| Component           | File                 | Responsibility                               |
| ------------------- | -------------------- | -------------------------------------------- |
| **Flight API**      | `flight_api.py`      | Amadeus API wrapper, flight search           |
| **Seat Manager**    | `seat_manager.py`    | Real-time seat reservation, timeout handling |
| **Dynamic Pricing** | `dynamic_pricing.py` | Demand-based fare calculation                |
| **Models**          | `models.py`          | User, Flight, Ticket, Seat, Place, Passenger |
| **Views**           | `views.py`           | All HTTP request handlers                    |

---

## 🛠️ Technology Stack

| Layer            | Technology                                |
| ---------------- | ----------------------------------------- |
| **Frontend**     | HTML5, CSS3, JavaScript, Django Templates |
| **Backend**      | Python 3.11, Django 3.1.2                 |
| **Database**     | PostgreSQL (Cloud SQL)                    |
| **External API** | Amadeus Flight Offers API                 |
| **Deployment**   | Google App Engine (Standard)              |
| **Static Files** | WhiteNoise middleware                     |

---

## 🔐 Security Features

- **CSRF Protection** - Django middleware
- **Password Hashing** - Django auth system
- **Card Validation** - Luhn algorithm (client + server)
- **Environment Variables** - API keys in `app.yaml` (not in code)
- **HTTPS Only** - App Engine enforced

---

## 📊 Database Schema (Key Models)

```
User ──┬── Ticket ──── Flight
       │      │
       │      └── Seat ──── Flight
       │
       └── Passenger
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Google Cloud Platform                  │
│  ┌─────────────────┐       ┌──────────────────────────┐ │
│  │   App Engine    │ ───── │    Cloud SQL             │ │
│  │   (Python 3.11) │       │    (PostgreSQL)          │ │
│  │                 │       │    flight-db instance    │ │
│  └─────────────────┘       └──────────────────────────┘ │
│           │                                              │
│           ▼                                              │
│  ┌─────────────────┐                                    │
│  │  Cloud Storage  │ (Static files, deployments)        │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
         │
         ▼ HTTPS
    ┌─────────┐
    │  Users  │  https://flight-app-2025.el.r.appspot.com
    └─────────┘
```

---

## 💡 Key Design Decisions

1. **API-First Flight Search** - Real-time data from Amadeus instead of static database
2. **Session-Based Seat Reservation** - 10-minute timeout prevents stale locks
3. **Dynamic Pricing** - Fares adjust based on demand and booking time
4. **Modular Architecture** - Separate files for API, seats, pricing
5. **Cloud-Native** - Designed for App Engine with Cloud SQL
