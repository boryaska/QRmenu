"""
URL configuration for qrmenu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import HomeView

urlpatterns = [
    # Главная страница
    path("", HomeView.as_view(), name="home"),
    
    # Админка
    path("admin/", admin.site.urls),
    
    # Аккаунты (регистрация, вход, профиль)
    path("accounts/", include("accounts.urls")),

    # Верификация ресторанов
    path("verification/", include("verification.urls")),

    # Каталог ресторанов для клиентов
    path("restaurants/", include("clients.urls", namespace="clients")),

    # Дашборд ресторана (приватные страницы)
    path("dashboard/", include("restaurants.urls", namespace="dashboard")),
    
    # Управление меню
    path("dashboard/menu/", include("menu.urls", namespace="menu")),
    
    # Управление заказами
    path("dashboard/orders/", include("orders.urls", namespace="orders")),
    
    # Публичные API (для клиентов)
    path("api/orders/", include("orders.api_urls")),
    
    # Публичное меню (доступно по QR-коду)
    path("m/", include("restaurants.public_urls", namespace="public")),
]

# Обслуживание медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Настройка админки
admin.site.site_header = "QR Menu Административная панель"
admin.site.site_title = "QR Menu Admin"
admin.site.index_title = "Добро пожаловать в панель управления QR Menu"
