from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.urls import reverse_lazy
from .models import Sponsor, Settlement, SponsorshipCategory, Place

class SponsorImagesAPIView(View):
    def get(self, request, *args, **kwargs):
        sponsors = Sponsor.objects.filter(logo__isnull=False).select_related('category')
        data = {}
        
        for sponsor in sponsors:
            if not sponsor.logo:
                continue
                
            category_name = sponsor.category.name if sponsor.category else "Uncategorized"
            if category_name not in data:
                data[category_name] = []
            
            data[category_name].append(sponsor.logo.url)
            
        return JsonResponse(data)

class SponsorDetailView(LoginRequiredMixin, DetailView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_detail.html'
    context_object_name = 'sponsor'



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.groups.filter(name='Conveners').exists() or user.is_superuser:
            context['is_convener'] = True
        return context

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'sponsorships/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Common context
        context['categories'] = SponsorshipCategory.objects.all()
        
        context['all_sponsors'] = Sponsor.objects.all()
        if user.groups.filter(name='Conveners').exists() or user.is_superuser:
            context['is_convener'] = True
            context['total_pledged'] = Sponsor.objects.aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0
            context['total_received'] = Settlement.objects.filter(status='VERIFIED').aggregate(Sum('amount'))['amount__sum'] or 0
            context['pending_settlements'] = Settlement.objects.filter(status='PENDING')
            
            # Convener Dashboard: Field Work
            context['global_places_visited'] = Place.objects.count()
            # Top performing coordinator by confirmed pledge amount from their visits
            top_coordinator = Sponsor.objects.filter(status='CONFIRMED', place__isnull=False).values('coordinator__username').annotate(total_amount=Sum('amount_pledged')).order_by('-total_amount').first()
            context['top_performing_coordinator'] = top_coordinator
            context['places'] = Place.objects.all()[:5] # Recent 5
            
        else:
            context['is_coordinator'] = True
            context['my_sponsors'] = Sponsor.objects.filter(coordinator=user)
            context['my_pledged'] = context['my_sponsors'].aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0
            context['my_received'] = Settlement.objects.filter(sponsor__coordinator=user, status='VERIFIED').aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Coordinator Dashboard: Field Work
            my_places = Place.objects.filter(visited_by=user)
            context['my_places_count'] = my_places.count()
            sponsors_from_visits = Sponsor.objects.filter(coordinator=user, place__isnull=False)
            context['sponsors_added_from_visits'] = sponsors_from_visits.count()
            context['positive_feedback_count'] = sponsors_from_visits.filter(feedback_type='POSITIVE').count()
            context['negative_feedback_count'] = sponsors_from_visits.filter(feedback_type='NEGATIVE').count()
            context['confirmed_sponsorship_amount'] = sponsors_from_visits.filter(status='CONFIRMED').aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0

        context['total_pledged'] = Sponsor.objects.aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0
        context['total_received'] = Settlement.objects.filter(status='VERIFIED').aggregate(Sum('amount'))['amount__sum'] or 0
        return context

class SponsorListView(LoginRequiredMixin, ListView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_list.html'
    context_object_name = 'sponsors'

    def get_queryset(self):
        # Only show confirmed or completed sponsors
        return Sponsor.objects.filter(status__in=['CONFIRMED', 'COMPLETED'])

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Sponsor
    template_name = 'sponsorships/organization_list.html'
    context_object_name = 'sponsors'

    def get_queryset(self):
        # Only show pending/visited organizations
        return Sponsor.objects.filter(status='PENDING')
class SponsorCreateView(LoginRequiredMixin, CreateView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_form.html'
    fields = ['name', 'place', 'poc_name', 'poc_phone', 'poc_email', 'feedback_type', 'feedback_notes', 'visit_date']
    success_url = reverse_lazy('sponsor_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_organization_log'] = True
        return context

    # We only prompt for initial contact fields. 
    # The user can later "Make Sponsor" which uses the full SponsorUpdateView

    def form_valid(self, form):
        form.instance.coordinator = self.request.user
        form.instance.status = 'PENDING' # Always default to PENDING for new visits
        return super().form_valid(form)

class SponsorUpdateView(LoginRequiredMixin, UpdateView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_form.html'
    fields = ['name', 'category', 'place', 'poc_name', 'poc_phone', 'poc_email', 'logo', 'amount_pledged', 'feedback_type', 'feedback_notes', 'visit_date', 'status']
    success_url = reverse_lazy('sponsor_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # If the user is trying to "Make Sponsor" (status = CONFIRMED), ensure category and amount are required.
        # We can enforce this strictly on POST by checking data.
        if self.request.method == 'POST':
            status = self.request.POST.get('status')
            if status == 'CONFIRMED':
                form.fields['category'].required = True
                form.fields['amount_pledged'].required = True
        return form

class PlaceListView(LoginRequiredMixin, ListView):
    model = Place
    template_name = 'sponsorships/place_list.html'
    context_object_name = 'places'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Conveners').exists() or user.is_superuser:
            return Place.objects.all()
        return Place.objects.filter(visited_by=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.groups.filter(name='Conveners').exists() or user.is_superuser:
            context['is_convener'] = True
        return context

class PlaceCreateView(LoginRequiredMixin, CreateView):
    model = Place
    template_name = 'sponsorships/place_form.html'
    fields = ['city', 'notes']
    success_url = reverse_lazy('place_list')

    def form_valid(self, form):
        form.instance.visited_by = self.request.user
        return super().form_valid(form)

class PlaceDetailView(LoginRequiredMixin, DetailView):
    model = Place
    template_name = 'sponsorships/place_detail.html'
    context_object_name = 'place'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.groups.filter(name='Conveners').exists() or user.is_superuser:
            context['is_convener'] = True
        return context

class SettlementCreateView(LoginRequiredMixin, CreateView):
    model = Settlement
    template_name = 'sponsorships/settlement_form.html'
    fields = ['sponsor', 'amount', 'date', 'reference_number', 'proof', 'notes']
    success_url = reverse_lazy('dashboard')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if not (user.groups.filter(name='Conveners').exists() or user.is_superuser):
            form.fields['sponsor'].queryset = Sponsor.objects.filter(coordinator=user)
        return form

class SettlementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Settlement
    template_name = 'sponsorships/settlement_form.html'
    fields = ['status', 'notes'] # Convener only updates status
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.groups.filter(name='Conveners').exists() or self.request.user.is_superuser

class FetchDemoView(TemplateView):
    template_name = 'sponsorships/fetch_demo.html'
