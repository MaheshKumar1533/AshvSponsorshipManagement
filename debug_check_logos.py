import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ashv_sponsorship.settings')
django.setup()

from sponsorships.models import Sponsor

def check_logos():
    total_sponsors = Sponsor.objects.count()
    sponsors_with_logo = Sponsor.objects.exclude(logo='').exclude(logo__isnull=True).count()
    
    print(f"Total Sponsors: {total_sponsors}")
    print(f"Sponsors with Logo: {sponsors_with_logo}")
    
    for s in Sponsor.objects.all():
        print(f"Sponsor: {s.name}, Logo: '{s.logo}'")

if __name__ == '__main__':
    check_logos()
