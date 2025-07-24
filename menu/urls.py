"""
URL configuration for menu app
"""
from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Категории
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Блюда
    path('dishes/', views.DishListView.as_view(), name='dishes'),
    path('dishes/create/', views.DishCreateView.as_view(), name='dish_create'),
    path('dishes/<int:pk>/', views.DishDetailView.as_view(), name='dish_detail'),
    path('dishes/<int:pk>/edit/', views.DishUpdateView.as_view(), name='dish_edit'),
    path('dishes/<int:pk>/delete/', views.DishDeleteView.as_view(), name='dish_delete'),
    path('dishes/<int:pk>/toggle-availability/', views.DishToggleAvailabilityView.as_view(), name='dish_toggle_availability'),
] 