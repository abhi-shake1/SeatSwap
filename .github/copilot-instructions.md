# Copilot Instructions for SeatSwap Railway Seat Exchange

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a Django-based railway seat exchange web application called "SeatSwap" that allows train passengers to exchange seats with other passengers traveling on the same route.

## Key Features
- User authentication and registration
- Seat listing and booking system
- PNR API integration for route validation
- UPI payment integration
- Admin panel for ticket checkers

## Technical Stack
- Backend: Django (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite (default Django)
- APIs: Railway PNR APIs

## Project Structure Guidelines
- Main app: `seats` - handles all seat exchange functionality
- Models: User profiles, seat listings, exchanges, payments
- Views: Class-based and function-based views for different functionalities
- Templates: HTML templates with Django template language
- Static files: CSS, JavaScript, images

## Development Guidelines
- Follow Django best practices
- Use Django's built-in authentication system
- Implement proper error handling
- Add form validation
- Use Django messages framework for user feedback
- Follow PEP 8 style guidelines
