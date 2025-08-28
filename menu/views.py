from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q, Count
from decimal import Decimal

from core.mixins import RestaurantOwnerMixin, FormValidationMixin, PaginationMixin, SearchMixin
from .models import Category, Dish, DishOption, DishIngredient
from .forms import CategoryForm, DishForm, DishOptionForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class CategoryListView(RestaurantOwnerMixin, SearchMixin, PaginationMixin, ListView):
    """
    Список категорий меню
    """
    model = Category
    template_name = 'menu/categories.html'
    context_object_name = 'categories'
    paginate_by = 12
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            dishes_count=Count('dishes')
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categories'] = self.get_queryset().count()
        context['active_categories'] = self.get_queryset().filter(is_active=True).count()
        return context


class CategoryCreateView(RestaurantOwnerMixin, FormValidationMixin, CreateView):
    """
    Создание категории
    """
    model = Category
    form_class = CategoryForm
    template_name = 'menu/category_form.html'
    success_url = reverse_lazy('menu:categories')

    def form_valid(self, form):
        form.instance.restaurant = self.get_restaurant()
        messages.success(self.request, 'Категория успешно создана!')
        return super().form_valid(form)


class CategoryUpdateView(RestaurantOwnerMixin, FormValidationMixin, UpdateView):
    """
    Редактирование категории
    """
    model = Category
    form_class = CategoryForm
    template_name = 'menu/category_form.html'
    success_url = reverse_lazy('menu:categories')

    def form_valid(self, form):
        messages.success(self.request, 'Категория успешно обновлена!')
        return super().form_valid(form)


class CategoryDeleteView(RestaurantOwnerMixin, DeleteView):
    """
    Удаление категории
    """
    model = Category
    template_name = 'menu/category_confirm_delete.html'
    success_url = reverse_lazy('menu:categories')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        dishes_count = category.dishes.count()
        
        if dishes_count > 0:
            messages.error(
                request, 
                f'Нельзя удалить категорию "{category.name}" - в ней есть {dishes_count} блюд.'
            )
            return redirect('menu:categories')
        
        messages.success(request, f'Категория "{category.name}" успешно удалена!')
        return super().delete(request, *args, **kwargs)


class DishListView(RestaurantOwnerMixin, SearchMixin, PaginationMixin, ListView):
    """
    Список блюд
    """
    model = Dish
    template_name = 'menu/dishes.html'
    context_object_name = 'dishes'
    paginate_by = 20
    search_fields = ['name', 'description', 'ingredients']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        
        # Фильтр по категории
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Фильтр по доступности
        is_available = self.request.GET.get('available')
        if is_available in ['true', 'false']:
            queryset = queryset.filter(is_available=is_available == 'true')
        
        # Фильтр по меткам
        if self.request.GET.get('popular'):
            queryset = queryset.filter(is_popular=True)
        if self.request.GET.get('new'):
            queryset = queryset.filter(is_new=True)
        if self.request.GET.get('vegetarian'):
            queryset = queryset.filter(is_vegetarian=True)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(restaurant=self.request.user.restaurantprofile)

        # Текущая категория для отображения
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                context['current_category'] = Category.objects.get(
                    pk=category_id,
                    restaurant=self.request.user.restaurantprofile
                )
            except Category.DoesNotExist:
                pass

        context['selected_available'] = self.request.GET.get('available', '')
        context['filter_popular'] = self.request.GET.get('popular', False)
        context['filter_new'] = self.request.GET.get('new', False)
        context['filter_vegetarian'] = self.request.GET.get('vegetarian', False)

        # Статистика
        all_dishes = Dish.objects.filter(restaurant=self.request.user.restaurantprofile)
        context['total_dishes'] = all_dishes.count()
        context['available_dishes'] = all_dishes.filter(is_available=True).count()
        context['popular_dishes'] = all_dishes.filter(is_popular=True).count()

        return context


class DishDetailView(RestaurantOwnerMixin, DetailView):
    """
    Детальный просмотр блюда
    """
    model = Dish
    template_name = 'menu/dish_detail.html'
    context_object_name = 'dish'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options'] = self.object.options.filter(is_available=True)
        context['ingredients'] = self.object.dish_ingredients.all()
        return context


class DishCreateView(RestaurantOwnerMixin, FormValidationMixin, CreateView):
    """
    Создание блюда
    """
    model = Dish
    form_class = DishForm
    template_name = 'menu/dish_form.html'
    
    def get_success_url(self):
        return reverse_lazy('menu:dish_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['restaurant'] = self.get_restaurant()
        return kwargs

    def form_valid(self, form):
        form.instance.restaurant = self.get_restaurant()
        messages.success(self.request, 'Блюдо успешно создано!')
        return super().form_valid(form)


class DishUpdateView(RestaurantOwnerMixin, FormValidationMixin, UpdateView):
    """
    Редактирование блюда
    """
    model = Dish
    form_class = DishForm
    template_name = 'menu/dish_form.html'
    
    def get_success_url(self):
        return reverse_lazy('menu:dish_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['restaurant'] = self.get_restaurant()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Блюдо успешно обновлено!')
        return super().form_valid(form)


class DishDeleteView(RestaurantOwnerMixin, DeleteView):
    """
    Удаление блюда
    """
    model = Dish
    template_name = 'menu/dish_confirm_delete.html'
    success_url = reverse_lazy('menu:dishes')

    def delete(self, request, *args, **kwargs):
        dish = self.get_object()
        messages.success(request, f'Блюдо "{dish.name}" успешно удалено!')
        return super().delete(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class DishToggleAvailabilityView(RestaurantOwnerMixin, DetailView):
    """
    Переключение доступности блюда (AJAX)
    """
    model = Dish

    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import json

        dish = self.get_object()

        # Получаем новый статус из запроса
        try:
            data = json.loads(request.body)
            new_status = data.get('is_available', not dish.is_available)
        except:
            new_status = not dish.is_available

        dish.is_available = new_status
        dish.save(update_fields=['is_available'])

        return JsonResponse({
            'success': True,
            'is_available': dish.is_available,
            'message': f'Блюдо "{dish.name}" теперь {"доступно" if dish.is_available else "недоступно"}!'
        })


@method_decorator(csrf_exempt, name='dispatch')
class CategoryToggleActiveView(RestaurantOwnerMixin, DetailView):
    """
    Переключение активности категории (AJAX)
    """
    model = Category

    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import json

        category = self.get_object()

        # Получаем новый статус из запроса
        try:
            data = json.loads(request.body)
            new_status = data.get('is_active', not category.is_active)
        except:
            new_status = not category.is_active

        category.is_active = new_status
        category.save(update_fields=['is_active'])

        return JsonResponse({
            'success': True,
            'is_active': category.is_active,
            'message': f'Категория "{category.name}" теперь {"активна" if category.is_active else "неактивна"}!'
        })
