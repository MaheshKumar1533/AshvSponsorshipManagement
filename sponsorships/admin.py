from django.contrib import admin
from sponsorships.models import *
# Register your models here.
admin.site.register(Sponsor)
admin.site.register(Settlement)
admin.site.register(SponsorshipCategory)