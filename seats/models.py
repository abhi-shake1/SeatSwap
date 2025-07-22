from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"


class SeatListing(models.Model):
    SEAT_TYPES = [
        ('LOWER', 'Lower'),
        ('MIDDLE', 'Middle'),
        ('UPPER', 'Upper'),
        ('SIDE_LOWER', 'Side Lower'),
        ('SIDE_UPPER', 'Side Upper'),
    ]
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BOOKED', 'Booked'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seat_listings')
    pnr_number = models.CharField(max_length=10)
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=100)
    source_station = models.CharField(max_length=100)
    destination_station = models.CharField(max_length=100)
    source_station_code = models.CharField(max_length=10)
    destination_station_code = models.CharField(max_length=10)
    journey_date = models.DateField()
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPES)
    seat_number = models.CharField(max_length=10)
    coach_number = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.train_name} - {self.seat_type} - {self.seat_number}"


class SeatExchange(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    seat_listing = models.ForeignKey(SeatListing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seat_purchases')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seat_sales')
    exchange_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    buyer_pnr = models.CharField(max_length=10)
    exchange_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-exchange_date']
    
    def __str__(self):
        return f"Exchange: {self.seller.username} -> {self.buyer.username}"


class PNRStatus(models.Model):
    pnr_number = models.CharField(max_length=10, unique=True)
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=100)
    source_station = models.CharField(max_length=100)
    destination_station = models.CharField(max_length=100)
    source_station_code = models.CharField(max_length=10)
    destination_station_code = models.CharField(max_length=10)
    journey_date = models.DateField()
    passenger_count = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PNR: {self.pnr_number} - {self.train_name}"


class StationCode(models.Model):
    station_code = models.CharField(max_length=10, unique=True)
    station_name = models.CharField(max_length=100)
    state = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.station_code} - {self.station_name}"
