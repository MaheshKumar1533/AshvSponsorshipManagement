from django.db import models
from django.contrib.auth.models import User

class SponsorshipCategory(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"

    class Meta:
        verbose_name_plural = "Sponsorship Categories"

class Place(models.Model):
    city = models.CharField(max_length=100)
    visited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='places_visited')
    visit_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.city}"
    
    @property
    def total_sponsors_contacted(self):
        return self.sponsors.count()
    
    @property
    def total_confirmed(self):
        return self.sponsors.filter(status='CONFIRMED').count()
    
    @property
    def total_rejected(self):
        return self.sponsors.filter(feedback_type='NEGATIVE').count()

    class Meta:
        ordering = ['-visit_date']

class Sponsor(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(SponsorshipCategory, on_delete=models.SET_NULL, null=True)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name='sponsors')
    poc_name = models.CharField(max_length=100, verbose_name="Point of Contact Name")
    poc_phone = models.CharField(max_length=20, verbose_name="Point of Contact Phone")
    poc_email = models.EmailField(verbose_name="Point of Contact Email")
    
    FEEDBACK_CHOICES = [
        ('POSITIVE', 'Positive'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral'),
    ]
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES, blank=True, null=True)
    feedback_notes = models.TextField(blank=True)
    visit_date = models.DateField(null=True, blank=True)

    logo = models.ImageField(upload_to='sponsor_logos/', blank=True, null=True)
    amount_pledged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sponsors')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.amount_pledged and self.category:
            self.amount_pledged = self.category.amount
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.status == 'CONFIRMED' and not self.logo:
            raise ValidationError({'logo': 'Logo is required when status is Confirmed.'})

    class Meta:
        ordering = ['-created_at']

    @property
    def total_settled_amount(self):
        return self.settlements.filter(status='VERIFIED').aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def balance_amount(self):
        return self.amount_pledged - self.total_settled_amount

class Settlement(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='settlements')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    reference_number = models.CharField(max_length=100, help_text="Transaction ID or Check Number")
    proof = models.FileField(upload_to='settlement_proofs/', blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_settlements')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sponsor.name} - {self.amount} ({self.status})"

    @property
    def is_image(self):
        if not self.proof:
            return False
        import os
        ext = os.path.splitext(self.proof.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
