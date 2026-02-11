from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from sponsorships.models import SponsorshipCategory, Sponsor, Settlement
from django.urls import reverse_lazy
from datetime import date

class SponsorshipTests(TestCase):
    def setUp(self):
        # Create Groups
        self.convener_group, _ = Group.objects.get_or_create(name='Conveners')
        self.coordinator_group, _ = Group.objects.get_or_create(name='Student Coordinators')

        # Create Users
        self.convener = User.objects.create_user(username='convener', password='password')
        self.convener.groups.add(self.convener_group)
        
        self.coordinator = User.objects.create_user(username='coordinator', password='password')
        self.coordinator.groups.add(self.coordinator_group)
        
        self.other_coordinator = User.objects.create_user(username='other_coord', password='password')
        self.other_coordinator.groups.add(self.coordinator_group)

        # Create Category
        self.category = SponsorshipCategory.objects.create(name='Gold Sponsor', amount=80000)

        # Create Sponsor
        self.sponsor = Sponsor.objects.create(
            name='Test Sponsor',
            category=self.category,
            poc_name='John Doe',
            poc_phone='1234567890',
            poc_email='john@example.com',
            coordinator=self.coordinator,
            status='CONFIRMED',
            amount_pledged=80000
        )

    def test_sponsor_balance(self):
        self.assertEqual(self.sponsor.balance_amount, 80000)
        
        # Add Settlement
        settlement = Settlement.objects.create(
            sponsor=self.sponsor,
            amount=50000,
            date=date.today(),
            reference_number='REF123',
            status='VERIFIED'
        )
        
        self.assertEqual(self.sponsor.total_settled_amount, 50000)
        self.assertEqual(self.sponsor.balance_amount, 30000)

    def test_coordinator_access(self):
        client = Client()
        client.login(username='coordinator', password='password')
        
        # Test Dashboard
        response = client.get(reverse_lazy('sponsor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Sponsor')
        
    def test_logo_upload(self):
        # This would require a dummy image file, skipping actual file upload test for simplicity
        # checking if field exists in form
        client = Client()
        client.login(username='coordinator', password='password')
        response = client.get(reverse_lazy('sponsor_add'))
        self.assertContains(response, 'type="file"')

    def test_sponsor_detail_view(self):
        client = Client()
        client.login(username='coordinator', password='password')
        # Create a settlement for the sponsor
        Settlement.objects.create(
            sponsor=self.sponsor,
            amount=10000,
            date='2024-01-01',
            reference_number='REF123',
            status='VERIFIED'
        )
        response = client.get(reverse_lazy('sponsor_detail', kwargs={'pk': self.sponsor.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sponsor.name)
        self.assertContains(response, 'REF123')
        self.assertContains(response, '10000')

    def test_sponsor_detail_view_as_convener(self):
        # Use existing convener
        convener = self.convener
        
        client = Client()
        client.login(username='convener', password='password')
        
        # Create a settlement for the sponsor
        Settlement.objects.create(
            sponsor=self.sponsor,
            amount=5000,
            date='2024-02-01',
            reference_number='REF456',
            status='PENDING'
        )
        
        response = client.get(reverse_lazy('sponsor_detail', kwargs={'pk': self.sponsor.pk}))
        self.assertEqual(response.status_code, 200)
        # Should verify that the 'Verify' button link is generated correctly, which would trigger the URL resolution
        self.assertContains(response, 'Verify')

        
        # Should not see other coordinator's sponsors if logic is correct?
        # Actually DashboardView context logic filters: user.groups.filter(name='Conveners').exists() or user.is_superuser:
        # else: my_sponsors = Sponsor.objects.filter(coordinator=user)
        # So yes.

    def test_convener_access(self):
        client = Client()
        client.login(username='convener', password='password')
        
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        # Total Target removed, checking for Total Pledged instead
        self.assertContains(response, 'Total Pledged')

    def test_settlement_creation(self):
        client = Client()
        client.login(username='coordinator', password='password')
        response = client.post('/settlements/add/', {
            'sponsor': self.sponsor.id,
            'amount': 10000,
            'date': date.today(),
            'reference_number': 'REF456',
            'notes': 'Test note'
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        self.assertEqual(Settlement.objects.filter(reference_number='REF456').count(), 1)

        self.assertEqual(Settlement.objects.filter(reference_number='REF456').count(), 1)

    def test_is_image_property(self):
        # Test with image extension
        settlement = Settlement(sponsor=self.sponsor, amount=100, date=date.today())
        settlement.proof.name = 'proof.jpg'
        self.assertTrue(settlement.is_image)
        
        settlement.proof.name = 'proof.PNG'
        self.assertTrue(settlement.is_image)
        
        # Test with non-image extension
        settlement.proof.name = 'proof.pdf'
        self.assertFalse(settlement.is_image)
        
        # Test with no proof
        settlement.proof = None
        self.assertFalse(settlement.is_image)

    def test_sponsor_images_api(self):
        # Assign logo to sponsor
        # self.sponsor.logo = 'sponsor_logos/test.jpg' # Logic in view checks for logo__isnull=False
        # But we need to mock or create a sponsor with logo.
        # Since we can't easily upload a file here without more setup, we can't fully test the query
        # UNLESS we manually set the logo field string (which works for FileField if no actual file ops done)
        self.sponsor.logo.name = 'sponsor_logos/test.jpg' 
        self.sponsor.save()
        
        client = Client()
        response = client.get(reverse_lazy('sponsor_images_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('Gold Sponsor', data)
        self.assertIn('/media/sponsor_logos/test.jpg', data['Gold Sponsor'])
