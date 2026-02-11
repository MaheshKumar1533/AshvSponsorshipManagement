import os
import django
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ashv_sponsorship.settings')
django.setup()

from sponsorships.models import Sponsor, SponsorshipCategory

def add_dummy_logo():
    sponsor = Sponsor.objects.first()
    if not sponsor:
        print("No sponsor found to update.")
        return

    print(f"Updating sponsor: {sponsor.name}")
    
    # Ensure directory exists
    if not os.path.exists('media/sponsor_logos'):
        os.makedirs('media/sponsor_logos')
        
    # Check if default logo exists
    if os.path.exists('media/sponsor_logos/default.png'):
        sponsor.logo = 'sponsor_logos/default.png'
        sponsor.save()
        print(f"Updated {sponsor.name} with default logo.")
    else:
        print("default.png not found in media/sponsor_logos/")

if __name__ == '__main__':
    add_dummy_logo()
