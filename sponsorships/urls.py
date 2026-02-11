from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='sponsorships/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('sponsors/', views.SponsorListView.as_view(), name='sponsor_list'),
    path('sponsors/add/', views.SponsorCreateView.as_view(), name='sponsor_add'),
    path('sponsor/<int:pk>/', views.SponsorDetailView.as_view(), name='sponsor_detail'),
    path('sponsor/<int:pk>/edit/', views.SponsorUpdateView.as_view(), name='sponsor_edit'),
    
    path('settlements/add/', views.SettlementCreateView.as_view(), name='settlement_add'),
    path('settlements/<int:pk>/verify/', views.SettlementUpdateView.as_view(), name='settlement_verify'),
    
    path('api/sponsor-images/', views.SponsorImagesAPIView.as_view(), name='sponsor_images_api'),
]
