from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
import json
import requests
from .models import SeatListing, SeatExchange, UserProfile, PNRStatus, StationCode, PassengerDetails
from .forms import UserRegistrationForm, SeatListingForm, PNRForm, PNRLoginForm
from railway_api import get_railway_api_client


def home(request):
    """Home page view"""
    return render(request, 'seats/home.html')


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                upi_id=form.cleaned_data.get('upi_id', '')
            )
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'seats/register.html', {'form': form})


def login_view(request):
    """User login view with PNR verification"""
    if request.method == 'POST':
        if 'username' in request.POST:
            # Initial login step
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # User is authenticated, now ask for PNR
                request.session['pending_user_id'] = user.id
                return render(request, 'seats/pnr_login.html', {'form': PNRLoginForm()})
            else:
                messages.error(request, 'Invalid username or password.')
        elif 'pnr_number' in request.POST:
            # PNR verification step
            form = PNRLoginForm(request.POST)
            if form.is_valid():
                pnr_number = form.cleaned_data['pnr_number']
                user_id = request.session.get('pending_user_id')
                
                if user_id:
                    user = User.objects.get(id=user_id)
                    
                    # Fetch PNR data
                    pnr_data = fetch_pnr_status(pnr_number)
                    if pnr_data:
                        # Update user profile with journey details
                        user_profile, created = UserProfile.objects.get_or_create(user=user)
                        user_profile.current_pnr = pnr_number
                        user_profile.source_station = pnr_data.get('source_station', '')
                        user_profile.destination_station = pnr_data.get('destination_station', '')
                        user_profile.source_station_code = pnr_data.get('source_station_code', '')
                        user_profile.destination_station_code = pnr_data.get('destination_station_code', '')
                        user_profile.journey_date = pnr_data.get('journey_date')
                        user_profile.travel_class = pnr_data.get('travel_class', '')
                        user_profile.pnr_updated_at = timezone.now()
                        user_profile.save()
                        
                        # Complete login
                        login(request, user)
                        del request.session['pending_user_id']
                        messages.success(request, f'Welcome! Journey: {pnr_data.get("source_station")} → {pnr_data.get("destination_station")}')
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'Invalid PNR number or PNR data not found.')
                        return render(request, 'seats/pnr_login.html', {'form': form})
            else:
                return render(request, 'seats/pnr_login.html', {'form': form})
    
    return render(request, 'seats/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard view"""
    user_listings = SeatListing.objects.filter(owner=request.user).order_by('-created_at')
    user_purchases = SeatExchange.objects.filter(buyer=request.user).order_by('-exchange_date')
    user_sales = SeatExchange.objects.filter(seller=request.user).order_by('-exchange_date')
    
    # Get user's current journey details
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    context = {
        'user_listings': user_listings,
        'user_purchases': user_purchases,
        'user_sales': user_sales,
        'user_profile': user_profile,
    }
    return render(request, 'seats/dashboard.html', context)


@login_required
def update_journey(request):
    """Allow users to update their journey details"""
    if request.method == 'POST':
        form = PNRLoginForm(request.POST)
        if form.is_valid():
            pnr_number = form.cleaned_data['pnr_number']
            
            # Fetch PNR data
            pnr_data = fetch_pnr_status(pnr_number)
            if pnr_data:
                # Update user profile with journey details
                user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                user_profile.current_pnr = pnr_number
                user_profile.source_station = pnr_data.get('source_station', '')
                user_profile.destination_station = pnr_data.get('destination_station', '')
                user_profile.source_station_code = pnr_data.get('source_station_code', '')
                user_profile.destination_station_code = pnr_data.get('destination_station_code', '')
                user_profile.journey_date = pnr_data.get('journey_date')
                user_profile.travel_class = pnr_data.get('travel_class', '')
                user_profile.pnr_updated_at = timezone.now()
                user_profile.save()
                
                messages.success(request, f'Journey details updated! Route: {pnr_data.get("source_station")} → {pnr_data.get("destination_station")}')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid PNR number or PNR data not found.')
    else:
        form = PNRLoginForm()
    
    return render(request, 'seats/update_journey.html', {'form': form})


@login_required
def list_seat(request):
    """List a seat for exchange"""
    if request.method == 'POST':
        form = SeatListingForm(request.POST)
        if form.is_valid():
            seat_listing = form.save(commit=False)
            seat_listing.owner = request.user
            
            # Fetch PNR details
            pnr_data = fetch_pnr_status(seat_listing.pnr_number)
            if pnr_data:
                seat_listing.train_number = pnr_data.get('train_number', '')
                seat_listing.train_name = pnr_data.get('train_name', '')
                seat_listing.source_station = pnr_data.get('source_station', '')
                seat_listing.destination_station = pnr_data.get('destination_station', '')
                seat_listing.source_station_code = pnr_data.get('source_station_code', '')
                seat_listing.destination_station_code = pnr_data.get('destination_station_code', '')
                seat_listing.journey_date = pnr_data.get('journey_date', timezone.now().date())
            
            seat_listing.save()
            messages.success(request, 'Seat listed successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SeatListingForm()
    
    return render(request, 'seats/list_seat.html', {'form': form})


@login_required
def browse_seats(request):
    """Browse available seats based on user's journey"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        user_source = user_profile.source_station or user_profile.source_station_code
        user_destination = user_profile.destination_station or user_profile.destination_station_code
        user_journey_date = user_profile.journey_date
        user_travel_class = user_profile.travel_class
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please update your journey details to see relevant seats.')
        return redirect('dashboard')
    
    # If user hasn't set journey details, redirect to dashboard
    if not user_source or not user_destination:
        messages.warning(request, 'Please login with your current journey PNR to see relevant seat exchanges.')
        return redirect('dashboard')
    
    # Get search parameters from request (for additional filtering)
    search_source = request.GET.get('source_station', '')
    search_destination = request.GET.get('destination_station', '')
    search_date = request.GET.get('journey_date', '')
    
    # Base filter: same route as user's journey
    seats = SeatListing.objects.filter(
        status='AVAILABLE'
    ).exclude(owner=request.user)
    
    # Filter by user's journey route
    seats = seats.filter(
        Q(source_station__icontains=user_source) | Q(source_station_code__icontains=user_source),
        Q(destination_station__icontains=user_destination) | Q(destination_station_code__icontains=user_destination)
    )
    
    # Additional filtering based on search parameters
    if search_source:
        seats = seats.filter(
            Q(source_station__icontains=search_source) | Q(source_station_code__icontains=search_source)
        )
    
    if search_destination:
        seats = seats.filter(
            Q(destination_station__icontains=search_destination) | Q(destination_station_code__icontains=search_destination)
        )
    
    if search_date:
        seats = seats.filter(journey_date=search_date)
    elif user_journey_date:
        # If no search date specified, filter by user's journey date
        seats = seats.filter(journey_date=user_journey_date)
    
    # Optional: Filter by same travel class
    if user_travel_class:
        # You might want to add travel_class field to SeatListing model for better filtering
        pass
    
    context = {
        'seats': seats,
        'user_source': user_source,
        'user_destination': user_destination,
        'user_journey_date': user_journey_date,
        'user_travel_class': user_travel_class,
        'search_source': search_source,
        'search_destination': search_destination,
        'search_date': search_date,
    }
    return render(request, 'seats/browse_seats.html', context)


@login_required
def seat_detail(request, seat_id):
    """View seat details"""
    seat = get_object_or_404(SeatListing, id=seat_id, status='AVAILABLE')
    
    if request.method == 'POST':
        # Handle seat booking
        buyer_pnr = request.POST.get('buyer_pnr')
        if buyer_pnr:
            # Verify buyer's PNR has same route
            pnr_data = fetch_pnr_status(buyer_pnr)
            if pnr_data and (
                pnr_data.get('source_station_code') == seat.source_station_code and
                pnr_data.get('destination_station_code') == seat.destination_station_code
            ):
                # Create exchange record
                exchange = SeatExchange.objects.create(
                    seat_listing=seat,
                    buyer=request.user,
                    seller=seat.owner,
                    exchange_amount=seat.price,
                    buyer_pnr=buyer_pnr
                )
                seat.status = 'BOOKED'
                seat.save()
                
                messages.success(request, 'Seat booked successfully! Please complete the payment.')
                return redirect('payment', exchange_id=exchange.id)
            else:
                messages.error(request, 'PNR route does not match the seat route.')
        else:
            messages.error(request, 'Please enter your PNR number.')
    
    return render(request, 'seats/seat_detail.html', {'seat': seat})


@login_required
def payment(request, exchange_id):
    """Payment view"""
    exchange = get_object_or_404(SeatExchange, id=exchange_id, buyer=request.user)
    
    if request.method == 'POST':
        # Handle payment completion
        transaction_id = request.POST.get('transaction_id')
        if transaction_id:
            exchange.payment_transaction_id = transaction_id
            exchange.payment_status = 'PAID'
            exchange.completion_date = timezone.now()
            exchange.save()
            
            exchange.seat_listing.status = 'COMPLETED'
            exchange.seat_listing.save()
            
            messages.success(request, 'Payment completed successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please enter transaction ID.')
    
    return render(request, 'seats/payment.html', {'exchange': exchange})


@login_required
def verify_pnr(request):
    """AJAX view to verify PNR"""
    if request.method == 'POST':
        pnr_number = request.POST.get('pnr_number')
        
        pnr_data = fetch_pnr_status(pnr_number)
        
        if pnr_data:
            return JsonResponse({
                'success': True,
                'data': pnr_data
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'PNR verification failed. Please check the PNR number and try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def fetch_pnr_status(pnr_number):
    """Fetch PNR status from API"""
    try:
        # Check if we have cached data (extended to 24 hours to reduce API calls)
        try:
            pnr_status = PNRStatus.objects.get(pnr_number=pnr_number)
            # If cached data is less than 24 hours old, use it
            if (timezone.now() - pnr_status.last_updated).total_seconds() < 86400:  # 24 hours
                # Get passenger details for cached data
                passengers = []
                for passenger in pnr_status.passengers.all():
                    passengers.append({
                        'passenger_serial_number': passenger.passenger_serial_number,
                        'booking_status': passenger.booking_status,
                        'booking_coach_id': passenger.booking_coach_id,
                        'booking_berth_no': passenger.booking_berth_no,
                        'booking_berth_code': passenger.booking_berth_code,
                        'current_status': passenger.current_status,
                        'current_coach_id': passenger.current_coach_id,
                        'current_berth_no': passenger.current_berth_no,
                        'current_berth_code': passenger.current_berth_code,
                        'current_status_details': f"{passenger.current_status}/{passenger.current_coach_id}/{passenger.current_berth_no}/{passenger.current_berth_code}",
                    })
                
                return {
                    'train_number': pnr_status.train_number,
                    'train_name': pnr_status.train_name,
                    'source_station': pnr_status.source_station,
                    'destination_station': pnr_status.destination_station,
                    'source_station_code': pnr_status.source_station_code,
                    'destination_station_code': pnr_status.destination_station_code,
                    'journey_date': pnr_status.journey_date,
                    'passenger_count': pnr_status.passenger_count,
                    'travel_class': pnr_status.travel_class or 'N/A',  # Use stored travel class
                    'passengers': passengers,  # Add passenger details
                }
        except PNRStatus.DoesNotExist:
            pass
        
        # Get API client and fetch PNR status (only if not cached)
        api_client = get_railway_api_client()
        pnr_data = api_client.get_pnr_status(pnr_number)
        
        if pnr_data:
            # Store in database for caching
            pnr_status, created = PNRStatus.objects.update_or_create(
                pnr_number=pnr_number,
                defaults={
                    'train_number': pnr_data.get('train_number', ''),
                    'train_name': pnr_data.get('train_name', ''),
                    'source_station': pnr_data.get('source_station', ''),
                    'destination_station': pnr_data.get('destination_station', ''),
                    'source_station_code': pnr_data.get('source_station_code', ''),
                    'destination_station_code': pnr_data.get('destination_station_code', ''),
                    'journey_date': pnr_data.get('journey_date', timezone.now().date()),
                    'passenger_count': pnr_data.get('passenger_count', 1),
                    'travel_class': pnr_data.get('travel_class', ''),  # Now storing travel class
                }
            )
            
            # Clear existing passenger details and save new ones
            pnr_status.passengers.all().delete()
            passengers_data = pnr_data.get('passengers', [])
            for passenger_info in passengers_data:
                PassengerDetails.objects.create(
                    pnr_status=pnr_status,
                    passenger_serial_number=passenger_info.get('passenger_serial_number', 0),
                    booking_status=passenger_info.get('booking_status', ''),
                    booking_coach_id=passenger_info.get('booking_coach_id', ''),
                    booking_berth_no=passenger_info.get('booking_berth_no', 0),
                    booking_berth_code=passenger_info.get('booking_berth_code', ''),
                    current_status=passenger_info.get('current_status', ''),
                    current_coach_id=passenger_info.get('current_coach_id', ''),
                    current_berth_no=passenger_info.get('current_berth_no', 0),
                    current_berth_code=passenger_info.get('current_berth_code', ''),
                )
            
            return pnr_data
        
        return None
        
    except Exception as e:
        print(f"Error fetching PNR status: {e}")
        return None


def get_station_name(station_code):
    """Get station name from code"""
    try:
        # First check local database
        station = StationCode.objects.get(station_code=station_code)
        return station.station_name
    except StationCode.DoesNotExist:
        # If not found locally, try API
        try:
            api_client = get_railway_api_client()
            station_name = api_client.get_station_name(station_code)
            
            # Store in database for future use
            if station_name != station_code:
                StationCode.objects.create(
                    station_code=station_code,
                    station_name=station_name
                )
            
            return station_name
            
        except Exception as e:
            print(f"Error fetching station name: {e}")
            return station_code


def fetch_train_schedule(train_number):
    """Fetch train schedule from API"""
    try:
        # Get API client and fetch train schedule
        api_client = get_railway_api_client()
        schedule_data = api_client.get_train_schedule(train_number)
        
        return schedule_data
        
    except Exception as e:
        print(f"Error fetching train schedule: {e}")
        return []


# Admin views for ticket checkers
@login_required
def admin_exchanges(request):
    """Admin view for ticket checkers"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    exchanges = SeatExchange.objects.filter(
        payment_status='PAID'
    ).order_by('-exchange_date')
    
    return render(request, 'seats/admin_exchanges.html', {'exchanges': exchanges})
