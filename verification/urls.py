from django.urls import path
from . import views

app_name = 'verification'

urlpatterns = [
    # Пользовательские views
    path('create/', views.RestaurantVerificationCreateView.as_view(), name='create'),
    path('edit/', views.RestaurantVerificationUpdateView.as_view(), name='edit'),
    path('edit-info/', views.RestaurantVerificationEditInfoView.as_view(), name='edit_info'),
    path('status/', views.RestaurantVerificationStatusView.as_view(), name='status'),

    # Админские views (для управления заявками)
    path('admin/<int:pk>/update/', views.RestaurantVerificationAdminUpdateView.as_view(), name='admin_update'),
]
