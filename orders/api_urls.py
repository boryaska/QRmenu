"""
Public API URLs for orders app
"""
from django.urls import path
from . import views

app_name = 'orders_api'

urlpatterns = [
    # Публичные API endpoints (для клиентов)
    path('api/<str:qr_data>/create/', views.CreateOrderAPIView.as_view(), name='create_order'),
    path('api/<str:qr_data>/dish/<int:dish_id>/', views.DishDetailAPIView.as_view(), name='dish_detail'),
] 