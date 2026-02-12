from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db.models import Sum
from django.urls import reverse_lazy
from .models import Sponsor, Settlement, SponsorshipCategory

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
            # Removed total_target as per request
            context['total_pledged'] = Sponsor.objects.aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0
            context['total_received'] = Settlement.objects.filter(status='VERIFIED').aggregate(Sum('amount'))['amount__sum'] or 0
            context['pending_settlements'] = Settlement.objects.filter(status='PENDING')
        else:
            context['is_coordinator'] = True
            context['my_sponsors'] = Sponsor.objects.filter(coordinator=user)
            context['my_pledged'] = context['my_sponsors'].aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0
            context['my_received'] = Settlement.objects.filter(sponsor__coordinator=user, status='VERIFIED').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_pledged'] = Sponsor.objects.aggregate(Sum('amount_pledged'))['amount_pledged__sum'] or 0
        context['total_received'] = Settlement.objects.filter(status='VERIFIED').aggregate(Sum('amount'))['amount__sum'] or 0
        return context

class SponsorListView(LoginRequiredMixin, ListView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_list.html'
    context_object_name = 'sponsors'



class SponsorCreateView(LoginRequiredMixin, CreateView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_form.html'
    fields = ['name', 'category', 'poc_name', 'poc_phone', 'poc_email', 'status']
    success_url = reverse_lazy('sponsor_list')

    def form_valid(self, form):
        form.instance.coordinator = self.request.user
        # Auto-set amount_pledged based on category if not provided? 
        # The model has amount_pledged. Let's add it to fields if we want to override, or set it from category.
        # But wait, amount_pledged is on Sponsor model. 
        # Let's say amount_pledged is automatically the category amount unless specified?
        # For simplicity, let's just make amount_pledged editable or auto-set.
        # Let's add 'amount_pledged' to fields for now.
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Maybe set initial amount_pledged if category is selected? Hard with server-side only.
        return form

# Redefine SponsorCreateView to include amount_pledged
class SponsorCreateView(LoginRequiredMixin, CreateView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_form.html'
    fields = ['name', 'category', 'poc_name', 'poc_phone', 'poc_email', 'logo', 'amount_pledged', 'status']
    success_url = reverse_lazy('sponsor_list')

    def form_valid(self, form):
        form.instance.coordinator = self.request.user
        return super().form_valid(form)

class SponsorUpdateView(LoginRequiredMixin, UpdateView):
    model = Sponsor
    template_name = 'sponsorships/sponsor_form.html'
    fields = ['name', 'category', 'poc_name', 'poc_phone', 'poc_email', 'logo', 'amount_pledged', 'status']
    success_url = reverse_lazy('sponsor_list')

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
