<p align="center">
  <img src="https://img.icons8.com/color/96/airplane-take-off.png" alt="Flight Booking Logo"/>
</p>

<h1 align="center">✈️ Flight Booking Application</h1>

<p align="center">
  <strong>A modern, feature-rich flight booking system built with Django</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Django-3.1+-green?style=for-the-badge&logo=django&logoColor=white" alt="Django"/>
  <img src="https://img.shields.io/badge/PostgreSQL-14+-blue?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Google_Cloud-Deployed-orange?style=for-the-badge&logo=google-cloud&logoColor=white" alt="GCP"/>
</p>

<p align="center">
  <a href="https://flight-app-2025.el.r.appspot.com">🌐 Live Demo</a> •
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-deployment">Deployment</a>
</p>

---

## 🌟 Overview

Flight Booking Application is a comprehensive airline reservation system that allows users to search flights, select seats, make bookings, and process payments. Built with Django and deployed on Google Cloud Platform with Cloud SQL PostgreSQL database.

---

## ✨ Features

### 🔍 Flight Search

- **Multi-city Search**: Search flights between any two airports
- **One-way & Round-trip**: Support for both trip types
- **Class Selection**: Economy, Business, and First Class options
- **Date Validation**: Prevents booking on past dates
- **Smart Airport Search**: Autocomplete airport codes with city names

### 💰 Dynamic Pricing Algorithm

Our intelligent pricing system adjusts fares based on demand:

| Occupancy | Price Multiplier | Description            |
| --------- | ---------------- | ---------------------- |
| < 30%     | 0.85x            | 📉 Low Demand Discount |
| 30-50%    | 1.00x            | 📊 Normal Price        |
| 50-70%    | 1.15x            | 📈 Moderate Demand     |
| 70-85%    | 1.30x            | 🔥 High Demand         |
| > 85%     | 1.50x            | 🚀 Surge Pricing       |

**Time-based Adjustments:**

- 30+ days ahead: 10% early bird discount
- Last 3 days: 30% premium

### 🪑 Interactive Seat Selection

- **Visual Seat Map**: Real-time interactive seat layout
- **Seat Classes**: Color-coded by Economy/Business/First
- **Live Availability**: See available, reserved, and booked seats
- **Concurrency Control**: Row-level locking prevents double-booking
- **Temporary Reservation**: 10-minute hold while booking

### 💳 Secure Payment System

- **Card Validation**: Real-time validation of card details
  - 16-digit card number with formatting
  - Cardholder name validation
  - Expiry date validation (not in past)
  - CVV validation (3 digits)
- **Server-side Validation**: Double validation for security
- **Visual Feedback**: Success/error animations

### 📱 User Features

- **User Authentication**: Register, Login, Logout
- **Booking History**: View all past and upcoming bookings
- **Ticket Management**: View, print, and cancel tickets
- **Booking Reference**: Unique 6-character reference codes

### 🎨 Modern UI/UX

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Crimson Theme**: Consistent brand colors throughout
- **Smooth Animations**: Micro-interactions and transitions
- **Loading States**: Visual feedback during operations
- **Error Handling**: User-friendly error messages

---

## 🛠️ Tech Stack

| Category             | Technology                         |
| -------------------- | ---------------------------------- |
| **Backend**          | Django 3.1, Python 3.11            |
| **Database**         | PostgreSQL 14 (Cloud SQL)          |
| **Frontend**         | HTML5, CSS3, JavaScript, Bootstrap |
| **Deployment**       | Google App Engine Standard         |
| **Database Hosting** | Google Cloud SQL                   |
| **Static Files**     | WhiteNoise                         |
| **Server**           | Gunicorn                           |

---

## 📁 Project Structure

```
Flight-Booking-Application/
├── capstone/               # Django project settings
│   ├── settings.py         # Configuration (local/production)
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI application
├── flight/                 # Main application
│   ├── models.py           # Database models
│   ├── views.py            # View controllers
│   ├── urls.py             # App URL routing
│   ├── dynamic_pricing.py  # 💰 Pricing algorithm
│   ├── seat_manager.py     # 🪑 Seat management
│   ├── utils.py            # Helper functions
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, images
├── Data/                   # CSV data files
│   ├── airports.csv        # Airport information
│   └── domestic_flights.csv # Flight schedules
├── app.yaml                # GCP App Engine config
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🚀 Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/hasratmd697/Flight-Booking-Application.git
cd Flight-Booking-Application

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load initial data
python manage.py shell -c "from flight.utils import createWeekDays, addPlaces, addDomesticFlights; createWeekDays(); addPlaces(); addDomesticFlights()"

# Start development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## ☁️ Deployment

### Google Cloud Platform

The application is deployed on **Google App Engine** with **Cloud SQL PostgreSQL**.

**Live URL:** https://flight-app-2025.el.r.appspot.com

### Deployment Commands

```bash
# Set project
gcloud config set project flight-app-2025

# Deploy
gcloud app deploy app.yaml --quiet

# View logs
gcloud app logs tail -s default
```

### Cloud Resources

- **App Engine**: Standard Environment (Python 3.11)
- **Cloud SQL**: PostgreSQL 14 (db-f1-micro)
- **Region**: asia-south1 (Mumbai)

---

## 📊 Database Models

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │     │   Flight    │     │    Place    │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id          │     │ id          │     │ id          │
│ username    │     │ origin      │────▶│ city        │
│ email       │     │ destination │────▶│ airport     │
│ password    │     │ depart_time │     │ code        │
└─────────────┘     │ airline     │     │ country     │
       │            │ economy_fare│     └─────────────┘
       │            │ business_fare│
       │            │ first_fare  │
       ▼            └─────────────┘
┌─────────────┐            │
│   Ticket    │            │
├─────────────┤            │
│ id          │            │
│ ref_no      │◀───────────┘
│ user        │
│ flight      │     ┌─────────────┐
│ seat_class  │     │    Seat     │
│ total_fare  │     ├─────────────┤
│ status      │     │ flight      │
│ booking_date│     │ seat_number │
└─────────────┘     │ seat_class  │
       │            │ status      │
       ▼            │ price       │
┌─────────────┐     └─────────────┘
│  Passenger  │
├─────────────┤
│ first_name  │
│ last_name   │
│ gender      │
└─────────────┘
```

---

## 🔧 API Endpoints

### Flight Search

```
GET /flight?TripType=1&Origin=DEL&Destination=BOM&DepartDate=2025-12-15&SeatClass=economy
```

### Dynamic Pricing

```
GET /api/pricing/flight?flight_id=1&seat_class=economy&departure_date=2025-12-15
```

### Seat Management

```
GET  /api/seats/available?flight_id=1
POST /api/seats/reserve   {seat_id, user_id}
POST /api/seats/release   {seat_id}
POST /api/seats/confirm   {seat_ids[], ticket_id}
```

---

## 📸 Screenshots

### Home Page

Beautiful landing page with flight search functionality

### Flight Search Results

Dynamic pricing with demand indicators

### Seat Selection

Interactive seat map with real-time availability

### Payment

Secure payment with card validation

---

## 🔐 Security Features

- **CSRF Protection**: All forms protected against CSRF attacks
- **SQL Injection Prevention**: Django ORM parameterized queries
- **Password Hashing**: Secure password storage
- **Server-side Validation**: All inputs validated on server
- **Environment Variables**: Sensitive data in environment

---

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test flight
```

---

## 📈 Future Enhancements

- [ ] Email notifications for bookings
- [ ] Payment gateway integration (Razorpay/Stripe)
- [ ] PDF ticket generation (currently disabled)
- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Real-time flight status updates

---

## 👨‍💻 Author

**Hasrat**

- GitHub: [@hasratmd697](https://github.com/hasratmd697)
- Email: hasratmd697@gmail.com

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Django Documentation
- Google Cloud Platform
- Bootstrap Team
- Icons8 for icons

---

<p align="center">
  Made with ❤️ by Hasrat MD
</p>

<p align="center">
  <a href="#-flight-booking-application">⬆️ Back to Top</a>
</p>
