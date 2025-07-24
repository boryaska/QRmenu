"""
URL configuration for orders app
"""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Основные страницы заказов
    path('', views.OrderListView.as_view(), name='orders'),
    path('dashboard/', views.OrderDashboardView.as_view(), name='dashboard'),
    path('stats/', views.OrderStatsView.as_view(), name='stats'),
    
    # Детальные страницы заказов
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/edit/', views.OrderUpdateView.as_view(), name='order_edit'),
    
    # Управление статусом и оплатой
    path('<int:pk>/status/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('<int:pk>/payment/', views.OrderPaymentUpdateView.as_view(), name='order_payment_update'),
    
    # API для AJAX обновлений
    path('<int:pk>/api/status/', views.OrderStatusAPIView.as_view(), name='order_status_api'),
] 