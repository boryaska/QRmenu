from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied

from core.utils import generate_qr_code
from .models import RestaurantProfile, RestaurantSettings
from .forms import RestaurantProfileForm, RestaurantSettingsForm


class RestaurantOwnerMixin:
    """
    Миксин для проверки, что пользователь является владельцем ресторана
    """
    def get_restaurant(self):
        """
        Получает ресторан текущего пользователя
        """
        if not hasattr(self.request.user, 'restaurantprofile'):
            raise PermissionDenied("У пользователя нет профиля ресторана")
        return self.request.user.restaurantprofile

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)


# === DASHBOARD VIEWS (для владельцев ресторанов) ===

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Главная страница дашборда ресторана
    """
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_restaurant'] = hasattr(self.request.user, 'restaurantprofile')
        
        if context['has_restaurant']:
            restaurant = self.request.user.restaurantprofile
            context['restaurant'] = restaurant
            # Базовая статистика
            context['stats'] = {
                'active_dishes': restaurant.get_active_dishes_count(),
                'active_categories': restaurant.get_active_categories_count(),
                'total_orders': 0,  # Заполним когда создадим модели заказов
                'revenue_today': 0,
            }
        
        return context


class RestaurantProfileCreateView(LoginRequiredMixin, CreateView):
    """
    Создание профиля ресторана
    """
    model = RestaurantProfile
    form_class = RestaurantProfileForm
    template_name = 'dashboard/profile_create.html'
    success_url = reverse_lazy('dashboard:profile')

    def dispatch(self, request, *args, **kwargs):
        # Если у пользователя уже есть ресторан, перенаправляем на редактирование
        if hasattr(request.user, 'restaurantprofile'):
            return redirect('dashboard:profile_edit')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Создаем настройки ресторана
        RestaurantSettings.objects.create(restaurant=self.object)
        
        messages.success(self.request, 'Профиль ресторана успешно создан!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class RestaurantProfileView(RestaurantOwnerMixin, DetailView):
    """
    Просмотр профиля ресторана
    """
    model = RestaurantProfile
    template_name = 'dashboard/profile.html'
    context_object_name = 'restaurant'

    def get_object(self):
        return self.get_restaurant()


class RestaurantProfileUpdateView(RestaurantOwnerMixin, UpdateView):
    """
    Редактирование профиля ресторана
    """
    model = RestaurantProfile
    form_class = RestaurantProfileForm
    template_name = 'dashboard/profile_edit.html'
    success_url = reverse_lazy('dashboard:profile')

    def get_object(self):
        return self.get_restaurant()

    def form_valid(self, form):
        messages.success(self.request, 'Профиль ресторана успешно обновлен!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class RestaurantSettingsView(RestaurantOwnerMixin, UpdateView):
    """
    Настройки ресторана
    """
    model = RestaurantSettings
    form_class = RestaurantSettingsForm
    template_name = 'dashboard/settings.html'
    success_url = reverse_lazy('dashboard:settings')

    def get_object(self):
        restaurant = self.get_restaurant()
        settings_obj, created = RestaurantSettings.objects.get_or_create(
            restaurant=restaurant
        )
        return settings_obj

    def form_valid(self, form):
        messages.success(self.request, 'Настройки успешно сохранены!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class QRCodeView(RestaurantOwnerMixin, TemplateView):
    """
    Просмотр и управление QR-кодом
    """
    template_name = 'dashboard/qr_code.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.get_restaurant()
        
        context['restaurant'] = restaurant
        context['qr_data'] = restaurant.qr_data
        context['menu_url'] = restaurant.get_menu_url()
        context['has_qr_code'] = bool(restaurant.qr_code)
        
        return context

    def post(self, request, *args, **kwargs):
        """
        Генерация нового QR-кода
        """
        restaurant = self.get_restaurant()
        
        try:
            # Генерируем QR-код
            menu_url = restaurant.get_menu_url()
            qr_file = generate_qr_code(menu_url)
            
            # Сохраняем QR-код
            restaurant.qr_code.save(
                f'qr_{restaurant.qr_data}.png',
                qr_file,
                save=True
            )
            
            messages.success(request, 'QR-код успешно сгенерирован!')
        except Exception as e:
            messages.error(request, 'Ошибка генерации QR-кода. Попробуйте еще раз.')
        
        return redirect('dashboard:qr_code')


class QRCodeDownloadView(RestaurantOwnerMixin, DetailView):
    """
    Скачивание QR-кода
    """
    def get(self, request, *args, **kwargs):
        restaurant = self.get_restaurant()
        
        if not restaurant.qr_code:
            raise Http404("QR-код не найден")
        
        try:
            with open(restaurant.qr_code.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/png')
                response['Content-Disposition'] = f'attachment; filename="qr_menu_{restaurant.name}.png"'
                return response
        except FileNotFoundError:
            raise Http404("Файл QR-кода не найден")


# === PUBLIC VIEWS (для клиентов по QR-коду) ===

class PublicMenuView(DetailView):
    """
    Публичное меню ресторана (доступно по QR-коду)
    """
    model = RestaurantProfile
    template_name = 'public/menu.html'
    context_object_name = 'restaurant'
    slug_field = 'qr_data'
    slug_url_kwarg = 'qr_data'

    def get_object(self):
        qr_data = self.kwargs.get('qr_data')
        try:
            restaurant = RestaurantProfile.objects.get(qr_data=qr_data)
            if not restaurant.is_active:
                raise Http404("Ресторан временно недоступен")
            return restaurant
        except RestaurantProfile.DoesNotExist:
            raise Http404("Ресторан не найден")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.object
        
        # Здесь будет логика получения меню (категории и блюда)
        # Пока заглушка
        context['categories'] = []  # restaurant.categories.filter(is_active=True)
        context['dishes'] = []      # restaurant.dishes.filter(is_available=True)
        context['qr_data'] = restaurant.qr_data
        
        return context


class PublicRestaurantInfoView(DetailView):
    """
    Публичная информация о ресторане
    """
    model = RestaurantProfile
    template_name = 'public/restaurant_info.html'
    context_object_name = 'restaurant'
    slug_field = 'qr_data'
    slug_url_kwarg = 'qr_data'

    def get_object(self):
        qr_data = self.kwargs.get('qr_data')
        try:
            return RestaurantProfile.objects.get(qr_data=qr_data)
        except RestaurantProfile.DoesNotExist:
            raise Http404("Ресторан не найден")


class PublicDishDetailView(DetailView):
    """
    Детали блюда для клиентов
    """
    template_name = 'public/dish_detail.html'

    def get(self, request, qr_data, dish_id):
        # Проверяем существование ресторана
        try:
            restaurant = RestaurantProfile.objects.get(qr_data=qr_data)
            if not restaurant.is_active:
                raise Http404("Ресторан временно недоступен")
        except RestaurantProfile.DoesNotExist:
            raise Http404("Ресторан не найден")

        # TODO: Получение блюда по ID
        # dish = get_object_or_404(Dish, id=dish_id, restaurant=restaurant, is_available=True)
        
        context = {
            'restaurant': restaurant,
            'qr_data': qr_data,
            # 'dish': dish,
        }
        
        return render(request, self.template_name, context)


# === ANALYTICS VIEWS ===

class AnalyticsView(RestaurantOwnerMixin, TemplateView):
    """
    Аналитика ресторана
    """
    template_name = 'dashboard/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.get_restaurant()
        
        # Базовая статистика (заполним когда создадим модели заказов)
        context['analytics'] = {
            'total_orders': 0,
            'total_revenue': 0,
            'active_dishes': restaurant.get_active_dishes_count(),
            'active_categories': restaurant.get_active_categories_count(),
            'popular_dishes': [],
            'revenue_chart_data': [],
            'orders_chart_data': [],
        }
        
        return context
