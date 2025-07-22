from django.contrib import admin
from .models import UserProfile, SeatListing, SeatExchange, PNRStatus, StationCode


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'upi_id', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'phone_number', 'upi_id']


@admin.register(SeatListing)
class SeatListingAdmin(admin.ModelAdmin):
    list_display = ['owner', 'pnr_number', 'train_name', 'source_station', 'destination_station', 
                   'seat_type', 'seat_number', 'price', 'status', 'created_at']
    list_filter = ['status', 'seat_type', 'journey_date', 'created_at']
    search_fields = ['pnr_number', 'train_name', 'source_station', 'destination_station', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SeatExchange)
class SeatExchangeAdmin(admin.ModelAdmin):
    list_display = ['seat_listing', 'buyer', 'seller', 'exchange_amount', 'payment_status', 'exchange_date']
    list_filter = ['payment_status', 'exchange_date']
    search_fields = ['buyer__username', 'seller__username', 'seat_listing__train_name', 'payment_transaction_id']
    readonly_fields = ['exchange_date', 'completion_date']


@admin.register(PNRStatus)
class PNRStatusAdmin(admin.ModelAdmin):
    list_display = ['pnr_number', 'train_name', 'source_station', 'destination_station', 'journey_date', 'last_updated']
    list_filter = ['journey_date', 'last_updated']
    search_fields = ['pnr_number', 'train_name', 'source_station', 'destination_station']
    readonly_fields = ['last_updated']


@admin.register(StationCode)
class StationCodeAdmin(admin.ModelAdmin):
    list_display = ['station_code', 'station_name', 'state']
    list_filter = ['state']
    search_fields = ['station_code', 'station_name', 'state']
