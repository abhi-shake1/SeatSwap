#!/usr/bin/env python
"""
Debug the journeyClass extraction issue
"""

import os

# Set environment variable BEFORE importing Django
os.environ['USE_REAL_API'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SeatSwap.settings')

import django
django.setup()

from railway_api import RapidAPIRailwayClient
import json

def debug_journey_class():
    """Debug the journey class extraction"""
    pnr = "2719553296"
    client = RapidAPIRailwayClient()
    
    print(f"Debugging journey class extraction for PNR: {pnr}")
    print("=" * 60)
    
    # Make raw API call first
    import http.client
    
    conn = http.client.HTTPSConnection(client.base_host)
    
    headers = {
        'x-rapidapi-key': client.api_key,
        'x-rapidapi-host': client.base_host
    }
    
    endpoint = f"/getPNRStatus/{pnr}"
    conn.request("GET", endpoint, headers=headers)
    
    res = conn.getresponse()
    data = res.read()
    
    if res.status == 200:
        api_data = json.loads(data.decode("utf-8"))
        data_section = api_data.get('data', {})
        
        print("Raw API Response - Key Fields:")
        print(f"  journeyClass: '{data_section.get('journeyClass', 'NOT_FOUND')}'")
        print(f"  trainNumber: '{data_section.get('trainNumber', 'NOT_FOUND')}'")
        print(f"  trainName: '{data_section.get('trainName', 'NOT_FOUND')}'")
        
        # Now test the processed version
        print("\nProcessed Response:")
        processed = client.get_pnr_status(pnr)
        
        if processed:
            print(f"  travel_class: '{processed.get('travel_class', 'NOT_FOUND')}'")
            print(f"  train_number: '{processed.get('train_number', 'NOT_FOUND')}'")
            print(f"  train_name: '{processed.get('train_name', 'NOT_FOUND')}'")
            
            # Debug the _process_pnr_data method
            print("\nDetailed Debug:")
            print(f"  Raw journeyClass value: {repr(data_section.get('journeyClass'))}")
            print(f"  Raw journeyClass type: {type(data_section.get('journeyClass'))}")
            
            # Check if there are any hidden characters or issues
            journey_class = data_section.get('journeyClass', '')
            if journey_class:
                print(f"  journeyClass length: {len(journey_class)}")
                print(f"  journeyClass bytes: {journey_class.encode('utf-8')}")
            
        else:
            print("  ❌ Processed response is None")
    
    else:
        print(f"❌ API Error: {res.status}")

def test_django_views():
    """Test the Django views to see what they return"""
    print("\n" + "=" * 60)
    print("Testing Django Views Integration")
    print("=" * 60)
    
    from seats.views import fetch_pnr_status
    
    # Clear cache first
    from seats.models import PNRStatus
    try:
        cached = PNRStatus.objects.get(pnr_number="2719553296")
        cached.delete()
        print("✅ Cleared cached data")
    except PNRStatus.DoesNotExist:
        print("ℹ️  No cached data to clear")
    
    # Fetch fresh data
    result = fetch_pnr_status("2719553296")
    
    if result:
        print("\nDjango fetch_pnr_status result:")
        for key, value in result.items():
            print(f"  {key}: '{value}' ({type(value).__name__})")
    else:
        print("❌ Django fetch_pnr_status returned None")

if __name__ == "__main__":
    debug_journey_class()
    test_django_views()
