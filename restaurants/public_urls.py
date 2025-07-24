"""
Public URLs for restaurants app (for QR code access)
"""
from django.urls import path
from . import views

app_name = 'restaurants_public'

urlpatterns = [
    # Публичное меню
    path('<str:qr_data>/', views.PublicMenuView.as_view(), name='public_menu'),
    path('<str:qr_data>/info/', views.PublicRestaurantInfoView.as_view(), name='public_info'),
    path('<str:qr_data>/dish/<int:dish_id>/', views.PublicDishDetailView.as_view(), name='public_dish_detail'),
] 