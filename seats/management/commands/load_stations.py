from django.core.management.base import BaseCommand
from seats.models import StationCode

class Command(BaseCommand):
    help = 'Load sample station codes'

    def handle(self, *args, **options):
        stations = [
            ('NDLS', 'New Delhi', 'Delhi'),
            ('BCT', 'Mumbai Central', 'Maharashtra'),
            ('HWH', 'Howrah Junction', 'West Bengal'),
            ('MAS', 'Chennai Central', 'Tamil Nadu'),
            ('SBC', 'Bengaluru City', 'Karnataka'),
            ('HYB', 'Hyderabad', 'Telangana'),
            ('PUNE', 'Pune Junction', 'Maharashtra'),
            ('JP', 'Jaipur Junction', 'Rajasthan'),
            ('LKO', 'Lucknow', 'Uttar Pradesh'),
            ('BPL', 'Bhopal Junction', 'Madhya Pradesh'),
            ('KOAA', 'Kolkata', 'West Bengal'),
            ('ADI', 'Ahmedabad Junction', 'Gujarat'),
            ('BBS', 'Bhubaneswar', 'Odisha'),
            ('TVC', 'Thiruvananthapuram Central', 'Kerala'),
            ('GHY', 'Guwahati', 'Assam'),
            ('PNBE', 'Patna Junction', 'Bihar'),
            ('CDG', 'Chandigarh', 'Chandigarh'),
            ('JU', 'Jodhpur Junction', 'Rajasthan'),
            ('UDZ', 'Udaipur City', 'Rajasthan'),
            ('BKN', 'Bikaner Junction', 'Rajasthan'),
        ]
        
        for code, name, state in stations:
            station, created = StationCode.objects.get_or_create(
                station_code=code,
                defaults={'station_name': name, 'state': state}
            )
            if created:
                self.stdout.write(f'Created station: {code} - {name}')
            else:
                self.stdout.write(f'Station already exists: {code} - {name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded station codes'))
