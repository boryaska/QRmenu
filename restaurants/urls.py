"""
URL configuration for restaurants app
"""
from django.urls import path
from . import views

app_name = 'restaurants'

# Dashboard URLs (для владельцев ресторанов)
dashboard_urlpatterns = [
    # Главная дашборда
    path('', views.DashboardView.as_view(), name='index'),
    
    # Профиль ресторана
    path('profile/', views.RestaurantProfileView.as_view(), name='profile'),
    path('profile/create/', views.RestaurantProfileCreateView.as_view(), name='profile_create'),
    path('profile/edit/', views.RestaurantProfileUpdateView.as_view(), name='profile_edit'),
    
    # Настройки ресторана
    path('settings/', views.RestaurantSettingsView.as_view(), name='settings'),
    
    # QR-код и ссылки
    path('qr/', views.QRCodeView.as_view(), name='qr_code'),
    path('qr/download/', views.QRCodeDownloadView.as_view(), name='qr_code_download'),
    
    # Аналитика
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]

# Public URLs (для клиентов по QR-коду)
public_urlpatterns = [
    # Публичное меню
    path('<str:qr_data>/', views.PublicMenuView.as_view(), name='public_menu'),
    path('<str:qr_data>/info/', views.PublicRestaurantInfoView.as_view(), name='public_info'),
    path('<str:qr_data>/dish/<int:dish_id>/', views.PublicDishDetailView.as_view(), name='public_dish_detail'),
]

# Основные URL patterns
urlpatterns = dashboard_urlpatterns + public_urlpatterns 