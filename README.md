# Flight Booking App

Hi! This is my flight booking project that I made using Python and Django. Its a simple website where you can book flights.

## What Can This App Do?

### 1. Search for Flights

- You can search flights from one city to another
- Pick one-way or round-trip
- Choose travel date (cant pick past dates)
- Select seat class (economy, business, first class)

### 2. Book Tickets

- Register and login to your account
- Book a flight after searching
- Get a booking reference number
- See all your bookings in one place

### 3. Pick Your Seat

- See a seat map like in real airlines
- Pick which seat you want
- Seats are color coded by class
- If someone else is booking same seat it wont let you

### 4. Make Payment

- Enter your card details to pay
- Card number validation
- Expiry date check
- CVV validation

### 5. Dynamic Pricing

- Price changes based on how full the flight is
- Early booking = cheaper tickets
- Last minute booking = more expensive
- This is how real airlines work too

### 6. User Accounts

- Create your own account
- Login and logout
- View your past bookings
- Cancel tickets if you want

## Technologies I Used

- Python (the coding language)
- Django (a framework for making websites)
- HTML and CSS (for the website look)
- JavaScript (for interactive stuff)
- SQLite/PostgreSQL (for storing data)

## How to Run This Project

1. Download the project
2. Open terminal in the folder
3. Create a virtual environment: `python -m venv .venv`
4. Activate it: `.\.venv\Scripts\activate` (on Windows)
5. Install stuff: `pip install -r requirements.txt`
6. Run migrations: `python manage.py migrate`
7. Start server: `python manage.py runserver`
8. Open browser and go to `http://127.0.0.1:8000`

## Live Demo

The application is deployed on Google App Engine with Cloud SQL PostgreSQL.

**Live URL:** https://flight-app-2025.el.r.appspot.com

## Folder Structure

- `capstone/` - main django settings
- `flight/` - all the flight booking code
- `Data/` - csv files with airport data
- `templates/` - html files
- `static/` - css and javascript files

## What I Learned

- How to make a website with Django
- How databases work
- User authentication
- Form validation
- CSS styling

## Future Ideas

- Add email notifications
- Connect real payment gateway
- Make a mobile app

---

Made by Hasrat Hussain

This is a Infosys Internship project. Feel free to use it and learn from it!
