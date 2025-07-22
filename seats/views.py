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
from .models import SeatListing, SeatExchange, UserProfile, PNRStatus, StationCode
from .forms import UserRegistrationForm, SeatListingForm, PNRForm
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
    """User login view"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
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
    
    context = {
        'user_listings': user_listings,
        'user_purchases': user_purchases,
        'user_sales': user_sales,
    }
    return render(request, 'seats/dashboard.html', context)


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
    """Browse available seats"""
    # Get user's current journey details from session or form
    source_station = request.GET.get('source_station', '')
    destination_station = request.GET.get('destination_station', '')
    journey_date = request.GET.get('journey_date', '')
    
    # Filter seats based on same route
    seats = SeatListing.objects.filter(
        status='AVAILABLE'
    ).exclude(owner=request.user)
    
    if source_station and destination_station:
        seats = seats.filter(
            Q(source_station__icontains=source_station) | Q(source_station_code__icontains=source_station),
            Q(destination_station__icontains=destination_station) | Q(destination_station_code__icontains=destination_station)
        )
    
    if journey_date:
        seats = seats.filter(journey_date=journey_date)
    
    context = {
        'seats': seats,
        'source_station': source_station,
        'destination_station': destination_station,
        'journey_date': journey_date,
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
                return {
                    'train_number': pnr_status.train_number,
                    'train_name': pnr_status.train_name,
                    'source_station': pnr_status.source_station,
                    'destination_station': pnr_status.destination_station,
                    'source_station_code': pnr_status.source_station_code,
                    'destination_station_code': pnr_status.destination_station_code,
                    'journey_date': pnr_status.journey_date,
                    'passenger_count': pnr_status.passenger_count,
                    'travel_class': 'N/A',  # Default since not stored in model
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
                    # Note: travel_class is not stored in PNRStatus model
                }
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
