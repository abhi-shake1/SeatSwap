# TrackEarn - Railway Seat Exchange Platform
#Link: http://trackearn.us-east-1.elasticbeanstalk.com/

A Django-based web application that allows railway passengers to exchange seats with other passengers traveling on the same route for a more comfortable journey.

## Features

### For Passengers
- **User Registration & Authentication**: Secure user accounts with profile management
- **Seat Listing**: List your seat for exchange with pricing
- **Seat Discovery**: Browse available seats on your route
- **PNR Integration**: Automatic journey details fetching using PNR API
- **Secure Payment**: UPI-based payment system for seat exchanges
- **Route Matching**: Only connects passengers with same source and destination

### For Ticket Checkers (Admin)
- **Exchange Monitoring**: View all completed seat exchanges
- **Admin Dashboard**: Manage users, listings, and transactions
- **Verification System**: Track exchange status and payment confirmations

## Technology Stack

- **Backend**: Django 5.1.2
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: SQLite (default, can be configured for PostgreSQL/MySQL)
- **APIs**: Railway PNR Status API, Station Code API
- **Payment**: UPI integration

## Installation & Setup

### Prerequisites
- Python 3.8+
- Django 5.1.2
- Internet connection for API calls

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MyProject
   ```

2. **Install dependencies**
   ```bash
   pip install django requests
   ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000`
   - Admin panel: `http://127.0.0.1:8000/admin`

## Project Structure

```
MyProject/
├── manage.py
├── SeatSwap/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── seats/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       └── seats/
│           ├── base.html
│           ├── home.html
│           ├── register.html
│           ├── login.html
│           ├── dashboard.html
│           ├── list_seat.html
│           ├── browse_seats.html
│           ├── seat_detail.html
│           └── payment.html
└── README.md
```

## How It Works

### 1. User Registration
- Passengers create accounts with username, email, phone number
- Optional UPI ID for receiving payments
- Secure authentication system

### 2. Seat Listing Process
- User enters their PNR number
- System fetches journey details automatically
- User specifies seat details (type, number, coach)
- Sets exchange price and description
- Seat becomes available for booking

### 3. Seat Discovery & Booking
- Users browse available seats filtered by route
- Route matching ensures same source/destination
- Users can view detailed seat information
- Booking requires buyer's PNR verification

### 4. Payment Process
- UPI-based payment between users
- Buyer pays seller directly using UPI ID
- Transaction ID confirmation system
- Status tracking for exchanges

### 5. Admin Monitoring
- Ticket checkers can view all exchanges
- Track payment status and completion
- User and listing management

## API Integration

The application is designed to integrate with:
- **PNR Status API**: For fetching journey details
- **Station Code API**: For station name/code conversion

*Note: Current implementation uses mock data. Replace with actual API endpoints in production.*

## Models

### UserProfile
- Extends Django's User model
- Stores phone number, UPI ID, verification status

### SeatListing
- Contains seat and journey information
- Links to PNR data and user
- Tracks pricing and availability status

### SeatExchange
- Records seat exchange transactions
- Tracks payment status and completion
- Links buyer and seller

### PNRStatus
- Caches PNR information
- Stores journey details for quick access

### StationCode
- Maps station codes to names
- Supports search functionality

## Security Features

- CSRF protection on all forms
- User authentication required for core features
- PNR verification for route matching
- Payment transaction tracking
- Admin-only access to sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support or questions, please contact the development team.

---

**SeatSwap** - Making railway journeys more comfortable, one seat exchange at a time! 🚂
