# ✈️ Flight Booking Application

A full-featured flight booking web application built with Django, featuring real-time flight search via the Amadeus API, interactive seat selection, dynamic pricing, and secure payment processing.

![Django](https://img.shields.io/badge/Django-3.1.2-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 🔍 Flight Search

- **Real-time API Integration** - Fetches live flight data from Amadeus Flight API
- **One-way & Round-trip Support** - Book single or return journeys
- **Flexible Date Selection** - Pick travel dates up to 3 months in advance
- **Multiple Seat Classes** - Economy, Business, and First Class options
- **Smart Filtering** - Filter by price, departure time, and arrival time

### 💺 Interactive Seat Selection

- **Visual Seat Map** - Airline-style seat layout for both outbound and return flights
- **Real-time Availability** - Seats update live with concurrent booking prevention
- **Seat Class Indicators** - Color-coded seats (available, selected, booked, premium)
- **Round-trip Flow** - Select seats for outbound first, then return flight
- **Auto-refresh** - Seat availability updates every 30 seconds

### 💳 Payment & Coupons

- **Credit Card Validation** - Luhn algorithm card number validation
- **Expiry Date Check** - Prevents expired cards
- **CVV Verification** - 3-digit security code validation
- **Coupon System** - Apply bank coupons (HDFC10, ICICI15, SBI500) for discounts
- **Hover Dropdown** - Quick coupon selection with discount preview

### 💰 Dynamic Pricing Algorithm

Prices automatically adjust based on demand and booking timing:

**📊 Occupancy-Based Multipliers (Seat Fill Rate):**

| Occupancy | Multiplier | Effect                          |
| --------- | ---------- | ------------------------------- |
| < 30%     | 0.85x      | 15% discount (attract bookings) |
| 30-50%    | 1.00x      | Base price                      |
| 50-70%    | 1.15x      | 15% increase                    |
| 70-85%    | 1.30x      | 30% increase (high demand)      |
| > 85%     | 1.50x      | 50% surge pricing               |

**⏱️ Time-Based Multipliers (Days to Departure):**

| Days  | Multiplier | Effect              |
| ----- | ---------- | ------------------- |
| > 30  | 0.90x      | Early bird discount |
| 15-30 | 1.00x      | Normal pricing      |
| 7-14  | 1.10x      | Moderate urgency    |
| 3-6   | 1.20x      | Last week premium   |
| < 3   | 1.30x      | Last minute surge   |

**Formula:** `Final Price = Base Price × Occupancy Multiplier × Time Multiplier`

**Example:** ₹5,000 ticket | 90% seats full | 1 day before departure  
`₹5,000 × 1.50 × 1.30 = ₹9,750`

### 👤 User Management

- **Registration & Login** - Secure authentication system
- **Booking History** - View all past and upcoming flights
- **Ticket Cancellation** - Cancel bookings when needed

## 🛠️ Technology Stack

| Category   | Technology                           |
| ---------- | ------------------------------------ |
| Backend    | Python 3.8+, Django 3.1.2            |
| Frontend   | HTML5, CSS3, JavaScript              |
| Database   | SQLite (dev), Neon PostgreSQL (prod) |
| API        | Amadeus Flight Offers API            |
| Deployment | Render                               |

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Flight-Booking-Application.git
cd Flight-Booking-Application

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
# AMADEUS_API_KEY=your_api_key
# AMADEUS_API_SECRET=your_api_secret

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000`

## 📁 Project Structure

```
Flight-Booking-Application/
├── capstone/              # Django project settings
│   ├── settings.py        # Configuration
│   ├── urls.py            # Main URL routing
│   └── utils.py           # PDF & ticket utilities
├── flight/                # Main application
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, JS, images
│   ├── models.py          # Database models
│   ├── views.py           # View controllers
│   ├── flight_api.py      # Amadeus API integration
│   ├── seat_manager.py    # Seat reservation logic
│   └── dynamic_pricing.py # Price calculation
├── Data/                  # Airport & flight data CSVs
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Amadeus API (for live flight data)
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret

# Database (for production)
DATABASE_URL=postgres://user:pass@host:port/dbname

# Security
SECRET_KEY=your_django_secret_key
DEBUG=True
```

## 📸 Screenshots

### Home Page

Search for flights with origin, destination, dates, and class selection.
<img width="1919" height="939" alt="Screenshot 2025-12-11 185534" src="https://github.com/user-attachments/assets/009bda7a-aef0-47b1-9656-1329c536466a" />

### Search Results

View available flights with prices, times, and duration.
<img width="1920" height="938" alt="Screenshot 2025-12-12 122036" src="https://github.com/user-attachments/assets/259efe07-2d8d-4d74-9d25-72d1fad020af" />

### Seat Selection

Interactive seat map with real-time availability.
<img width="1920" height="940" alt="Screenshot 2025-12-12 122156" src="https://github.com/user-attachments/assets/2c2f023d-423d-4d67-b7cd-1b4320303dba" />
<img width="1920" height="936" alt="Screenshot 2025-12-12 122256" src="https://github.com/user-attachments/assets/99200440-14bc-44a7-9f92-a9021c3edabc" />

### Payment

Secure checkout with coupon support.
<img width="1920" height="940" alt="Screenshot 2025-12-12 122434" src="https://github.com/user-attachments/assets/1d057aaf-334c-4d39-8db8-8d5f2eedb367" />

## 🌐 Live Demo

**Production URL:** https://flight-booking-app.onrender.com

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Recent Updates

- ✅ **Neon PostgreSQL Migration** - Persistent database with generous free tier
- ✅ **Amadeus API Integration** - Live flight search
- ✅ **Round-trip Seat Selection** - Select seats for both legs
- ✅ **Coupon System** - Bank card discounts (HDFC, ICICI, SBI)
- ✅ **Payment Validation** - Server-side card validation
- ✅ **Indian Rupee (₹)** - Proper currency display

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Hasrat Hussain**

Infosys Internship Project - 2025

---

⭐ If you found this project helpful, please give it a star!
