from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientHomeView.as_view(), name='home'),
    path('catalog/', views.RestaurantCatalogView.as_view(), name='catalog'),
    path('restaurant/<str:qr_data>/', views.RestaurantDetailView.as_view(), name='restaurant_detail'),
]
