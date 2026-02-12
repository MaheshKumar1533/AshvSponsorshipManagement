import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ashv_sponsorship.settings')
django.setup()

from sponsorships.models import SponsorshipCategory, Sponsor
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType

def populate():
    categories = [
        ("Title Sponsor", 300000),
        ("Co-Title Sponsor", 250000),
        ("Associate Title Sponsor", 200000),
        ("Platinum Sponsor", 150000),
        ("Diamond Sponsor", 100000),
        ("Gold Sponsor", 80000),
        ("Silver Sponsor", 60000),
        ("Sports (Prizes, Refreshments etc.)", 50000),
        ("Cultural (Costumes, Food, etc.)", 50000),
        ("Technical (Material, Kit, Food etc.)", 50000),
        ("Bank Partner", 50000),
        ("Media Partner", 50000),
    ]

    print("Creating Categories...")
    for name, amount in categories:
        SponsorshipCategory.objects.get_or_create(name=name, defaults={'amount': amount})
    print("Categories created.")

    print("Creating Groups...")
    convener_group, _ = Group.objects.get_or_create(name='Conveners')
    coordinator_group, _ = Group.objects.get_or_create(name='Student Coordinators')
    print("Groups created.")

    # Create Superuser if not exists
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Superuser 'admin' created.")
    else:
        print("Superuser 'admin' already exists.")

    # Create a dummy sponsor
    try:
        category = SponsorshipCategory.objects.first()
        sponsor, created = Sponsor.objects.get_or_create(
            name="Dummy Sponsor",
            defaults={
                'category': category,
                'poc_name': "John Doe",
                'poc_phone': "1234567890",
                'poc_email': "john@example.com",
                'status': "CONFIRMED"
            }
        )
        if created:
            print("Dummy Sponsor created.")
        else:
            print("Dummy Sponsor already exists.")
    except Exception as e:
        print(f"Error creating dummy sponsor: {e}")

if __name__ == '__main__':
    populate()
