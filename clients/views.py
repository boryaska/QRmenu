from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q, Count
from restaurants.models import RestaurantProfile
from menu.models import Category, Dish


class RestaurantCatalogView(ListView):
    """
    Каталог ресторанов для клиентов
    """
    model = RestaurantProfile
    template_name = 'clients/catalog.html'
    context_object_name = 'restaurants'
    paginate_by = 12

    def get_queryset(self):
        queryset = RestaurantProfile.objects.filter(
            is_active=True
        ).select_related('user')

        # Поиск по названию
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query)
            )

        # Фильтр по адресу
        location_query = self.request.GET.get('location', '')
        if location_query:
            queryset = queryset.filter(
                Q(address__icontains=location_query)
            )

        # Сортировка
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'rating':
            # Заглушка для рейтинга (можно добавить позже)
            queryset = queryset.order_by('name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['location_query'] = self.request.GET.get('location', '')
        context['sort_by'] = self.request.GET.get('sort', 'name')
        return context


class RestaurantDetailView(DetailView):
    """
    Детальная страница ресторана
    """
    model = RestaurantProfile
    template_name = 'clients/restaurant_detail.html'
    context_object_name = 'restaurant'
    slug_field = 'qr_data'
    slug_url_kwarg = 'qr_data'

    def get_object(self):
        qr_data = self.kwargs.get('qr_data')
        restaurant = get_object_or_404(
            RestaurantProfile,
            qr_data=qr_data,
            is_active=True
        )
        return restaurant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.object

        # Получаем активные категории с блюдами
        categories = Category.objects.filter(
            restaurant=restaurant,
            is_active=True
        ).prefetch_related(
            'dishes'
        ).order_by('sort_order', 'name')

        # Добавляем только категории, у которых есть доступные блюда
        categories_with_dishes = []
        for category in categories:
            available_dishes = category.dishes.filter(
                is_available=True
            ).order_by('sort_order', 'name')

            if available_dishes.exists():
                category.available_dishes = available_dishes
                categories_with_dishes.append(category)

        context['categories'] = categories_with_dishes
        context['qr_data'] = restaurant.qr_data

        return context


class ClientHomeView(TemplateView):
    """
    Главная страница для клиентов
    """
    template_name = 'clients/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Популярные рестораны (по количеству блюд)
        popular_restaurants = RestaurantProfile.objects.filter(
            is_active=True
        ).annotate(
            dish_count=Count('dishes', filter=Q(dishes__is_available=True))
        ).order_by('-dish_count')[:6]

        # Новые рестораны
        new_restaurants = RestaurantProfile.objects.filter(
            is_active=True
        ).order_by('-created_at')[:6]

        context['popular_restaurants'] = popular_restaurants
        context['new_restaurants'] = new_restaurants

        return context
