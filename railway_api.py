"""
Railway API utilities for fetching PNR status, station information, and train schedules.
"""

import requests
import http.client
import json
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RapidAPIRailwayClient:
    """
    Client for interacting with RapidAPI IRCTC APIs
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or "f77026abbamsh55be46e64f1caadp116470jsn76f82eff6a44"
        self.base_host = "irctc-indian-railway-pnr-status.p.rapidapi.com"
        self.timeout = 10
        
    def get_pnr_status(self, pnr_number):
        """
        Get PNR status from RapidAPI IRCTC API
        
        Args:
            pnr_number (str): 10-digit PNR number
            
        Returns:
            dict: PNR status data or None if error
        """
        try:
            conn = http.client.HTTPSConnection(self.base_host)
            
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.base_host
            }
            
            endpoint = f"/getPNRStatus/{pnr_number}"
            conn.request("GET", endpoint, headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                api_data = json.loads(data.decode("utf-8"))
                
                # Check if response has success status
                if api_data.get('success') == True or api_data.get('status') == True:
                    return self._process_pnr_data(api_data)
                else:
                    logger.error(f"API error: {api_data.get('message', 'Unknown error')}")
                    return None
            elif res.status == 429:
                logger.error("Rate limit exceeded - too many API requests")
                return None
            else:
                logger.error(f"HTTP error: {res.status}")
                return None
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def get_station_name(self, station_code):
        """
        Get station name from station code using RapidAPI
        
        Args:
            station_code (str): Station code (e.g., 'NDLS')
            
        Returns:
            str: Station name or station code if not found
        """
        try:
            conn = http.client.HTTPSConnection(self.base_host)
            
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.base_host
            }
            
            endpoint = f"/api/v3/getStationByCode?stationCode={station_code}"
            conn.request("GET", endpoint, headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                api_data = json.loads(data.decode("utf-8"))
                
                if api_data.get('status') == True:
                    station_data = api_data.get('data', {})
                    return station_data.get('name', station_code)
                    
            return station_code
            
        except Exception as e:
            logger.error(f"Error getting station name: {e}")
            return station_code
    
    def get_train_schedule(self, train_number):
        """
        Get train schedule from RapidAPI
        
        Args:
            train_number (str): Train number (e.g., '12345')
            
        Returns:
            list: Train schedule data or empty list if error
        """
        try:
            conn = http.client.HTTPSConnection(self.base_host)
            
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.base_host
            }
            
            endpoint = f"/api/v3/trainSchedule?trainNumber={train_number}"
            conn.request("GET", endpoint, headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                api_data = json.loads(data.decode("utf-8"))
                
                if api_data.get('status') == True:
                    return api_data.get('data', [])
                    
            return []
            
        except Exception as e:
            logger.error(f"Error getting train schedule: {e}")
            return []
    
    def _process_pnr_data(self, api_data):
        """
        Process raw PNR data from API response
        
        Args:
            api_data (dict): Raw API response data
            
        Returns:
            dict: Processed PNR data
        """
        try:
            data = api_data.get('data', {})
            
            # Extract train information
            train_number = data.get('trainNumber', '')
            train_name = data.get('trainName', '')
            
            # Extract journey information
            from_station_code = data.get('sourceStation', '')
            to_station_code = data.get('destinationStation', '')
            
            # For station names, we'll use the codes as names for now
            # You can enhance this later with a station code to name mapping
            from_station_name = from_station_code
            to_station_name = to_station_code
            
            # Parse journey date
            journey_date_str = data.get('dateOfJourney', '')
            journey_date = timezone.now().date()
            
            if journey_date_str:
                try:
                    # API returns date in format like "Feb 9, 2025 11:30:05 AM"
                    # Extract just the date part
                    date_part = journey_date_str.split(' ')
                    if len(date_part) >= 3:
                        # Convert "Feb 9, 2025" to date
                        from datetime import datetime
                        date_str = f"{date_part[0]} {date_part[1].rstrip(',')}, {date_part[2]}"
                        journey_date = datetime.strptime(date_str, '%b %d, %Y').date()
                except (ValueError, IndexError):
                    # If parsing fails, use current date
                    journey_date = timezone.now().date()
            
            # Extract passenger information
            passengers = data.get('passengerList', [])
            passenger_count = data.get('numberOfpassenger', len(passengers))
            
            # Extract fare information
            booking_fare = data.get('bookingFare', 0)
            
            processed_data = {
                'train_number': train_number,
                'train_name': train_name,
                'source_station': from_station_name,
                'destination_station': to_station_name,
                'source_station_code': from_station_code,
                'destination_station_code': to_station_code,
                'journey_date': journey_date,
                'passenger_count': passenger_count,
                'chart_prepared': data.get('chartStatus', '').lower() != 'chart not prepared',
                'travel_class': data.get('journeyClass', ''),
                'booking_fare': str(booking_fare),
                'quota': data.get('quota', ''),
                'booking_date': data.get('bookingDate', ''),
                'arrival_date': data.get('arrivalDate', ''),
                'distance': data.get('distance', 0),
                'mobile_number': data.get('mobileNumber', ''),
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing PNR data: {e}")
            return None


# Mock API client for testing without actual API key
class MockRailwayAPIClient:
    """
    Mock client for testing purposes
    """
    
    def get_pnr_status(self, pnr_number):
        """Mock PNR status data"""
        # Different mock data based on PNR number for testing
        mock_data_sets = {
            '8634824688': {
                'train_number': '12185',
                'train_name': 'REWANCHAL EXP',
                'source_station': 'Rani Kamlapati(Bhopal)',
                'destination_station': 'Rewa',
                'source_station_code': 'RKMP',
                'destination_station_code': 'REWA',
                'journey_date': timezone.now().date(),
                'passenger_count': 4,
                'chart_prepared': False,
                'travel_class': '3A',
                'departure_time': '22:00',
                'arrival_time': '08:00',
                'duration': '10:0',
                'booking_fare': '3740',
                'quota': 'GN',
                'booking_date': '28-06-2025',
            },
            '4335734389': {
                'train_number': '17221',
                'train_name': 'COA LTT EXPRESS',
                'source_station': 'Kakinada Town',
                'destination_station': 'Secunderabad Junction',
                'source_station_code': 'CCT',
                'destination_station_code': 'SC',
                'journey_date': timezone.now().date(),
                'passenger_count': 1,
                'chart_prepared': True,
                'travel_class': 'SL',
                'departure_time': '19:45',
                'arrival_time': '06:45',
                'duration': '11:0',
                'booking_fare': '385',
                'quota': 'GN',
                'booking_date': '25-06-2025',
            },
            '1234567890': {
                'train_number': '18447',
                'train_name': 'HIRAKUD EXP',
                'source_station': 'Jagdalpur',
                'destination_station': 'Puri',
                'source_station_code': 'JDB',
                'destination_station_code': 'PURI',
                'journey_date': timezone.now().date(),
                'passenger_count': 2,
                'chart_prepared': False,
                'travel_class': '3A',
                'departure_time': '09:08',
                'arrival_time': '20:20',
                'duration': '11:12',
                'booking_fare': '855',
                'quota': 'GN',
                'booking_date': '27-08-2022',
            }
        }
        
        # Return specific mock data if available, otherwise default
        if pnr_number in mock_data_sets:
            return mock_data_sets[pnr_number]
        else:
            # Return default mock data for unknown PNRs
            return {
                'train_number': '12345',
                'train_name': 'TEST EXPRESS',
                'source_station': 'Test Station A',
                'destination_station': 'Test Station B',
                'source_station_code': 'TSA',
                'destination_station_code': 'TSB',
                'journey_date': timezone.now().date(),
                'passenger_count': 1,
                'chart_prepared': False,
                'travel_class': 'SL',
                'departure_time': '10:00',
                'arrival_time': '18:00',
                'duration': '8:0',
                'booking_fare': '500',
                'quota': 'GN',
                'booking_date': '01-01-2025',
            }
    
    def get_station_name(self, station_code):
        """Mock station name data"""
        # Simple mock mapping
        station_map = {
            'NDLS': 'New Delhi',
            'CSMT': 'Chhatrapati Shivaji Maharaj Terminus',
            'HWH': 'Howrah Junction',
            'MAS': 'Chennai Central',
            'SBC': 'Bangalore City',
            'PUNE': 'Pune Junction',
            'JP': 'Jaipur',
            'ADI': 'Ahmedabad Junction',
            'BPL': 'Bhopal Junction',
            'INDB': 'Indore Junction',
        }
        return station_map.get(station_code, station_code)
    
    def get_train_schedule(self, train_number):
        """Mock train schedule data"""
        # Simple mock schedule
        return [
            {
                'station_name': 'Source Station',
                'station_code': 'SRC',
                'arrival_time': '00:00',
                'departure_time': '10:00',
                'distance': 0,
                'day': 1
            },
            {
                'station_name': 'Intermediate Station',
                'station_code': 'INT',
                'arrival_time': '14:00',
                'departure_time': '14:05',
                'distance': 200,
                'day': 1
            },
            {
                'station_name': 'Destination Station',
                'station_code': 'DST',
                'arrival_time': '18:00',
                'departure_time': '18:00',
                'distance': 400,
                'day': 1
            }
        ]


def get_railway_api_client():
    """
    Get the appropriate Railway API client based on configuration
    
    Returns:
        IRailwayClient: API client instance
    """
    # For now, use mock client for testing
    # In production, uncomment the line below to use real API
    return MockRailwayAPIClient()
    # return RapidAPIRailwayClient()
