from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy


class RestaurantOwnerMixin(LoginRequiredMixin):
    """
    Миксин для проверки, что пользователь является владельцем ресторана
    Автоматически фильтрует все объекты по restaurant
    """
    
    def get_restaurant(self):
        """
        Получает ресторан текущего пользователя или выбрасывает ошибку
        """
        if not hasattr(self.request.user, 'restaurantprofile'):
            raise PermissionDenied("У пользователя нет профиля ресторана")
        return self.request.user.restaurantprofile

    def get_queryset(self):
        """
        Автоматически фильтрует queryset по ресторану пользователя
        """
        queryset = super().get_queryset()
        restaurant = self.get_restaurant()
        
        # Если модель имеет поле restaurant, фильтруем по нему
        if hasattr(queryset.model, 'restaurant'):
            return queryset.filter(restaurant=restaurant)
        
        return queryset

    def form_valid(self, form):
        """
        Автоматически устанавливает restaurant при сохранении формы
        """
        if hasattr(form.instance, 'restaurant'):
            form.instance.restaurant = self.get_restaurant()
        return super().form_valid(form)


class RestaurantObjectMixin(RestaurantOwnerMixin):
    """
    Миксин для работы с объектами, принадлежащими конкретному ресторану
    Проверяет, что объект принадлежит ресторану текущего пользователя
    """
    
    def get_object(self, queryset=None):
        """
        Получает объект и проверяет, что он принадлежит ресторану пользователя
        """
        obj = super().get_object(queryset)
        
        # Проверяем, что объект принадлежит ресторану пользователя
        if hasattr(obj, 'restaurant'):
            restaurant = self.get_restaurant()
            if obj.restaurant != restaurant:
                raise Http404("Объект не найден")
        
        return obj


class FormValidationMixin:
    """
    Миксин для унифицированной обработки форм с сообщениями
    """
    success_message = None
    error_message = "Пожалуйста, исправьте ошибки в форме."

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class FileUploadMixin:
    """
    Миксин для безопасной загрузки файлов
    """
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    max_file_size = 5 * 1024 * 1024  # 5MB

    def validate_file_upload(self, file):
        """
        Валидация загружаемых файлов
        """
        if not file:
            return True

        # Проверка расширения файла
        import os
        _, ext = os.path.splitext(file.name.lower())
        if ext not in self.allowed_extensions:
            raise ValidationError(
                f'Недопустимый тип файла. Разрешены: {", ".join(self.allowed_extensions)}'
            )

        # Проверка размера файла
        if file.size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            raise ValidationError(f'Файл слишком большой. Максимальный размер: {max_size_mb}MB')

        return True


class PaginationMixin:
    """
    Миксин для унифицированной пагинации
    """
    paginate_by = 20
    paginate_orphans = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем информацию о пагинации
        if 'page_obj' in context:
            page_obj = context['page_obj']
            context.update({
                'pagination_info': {
                    'current_page': page_obj.number,
                    'total_pages': page_obj.paginator.num_pages,
                    'total_items': page_obj.paginator.count,
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next(),
                    'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                    'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                }
            })
        
        return context


class SearchMixin:
    """
    Миксин для поиска по объектам
    """
    search_fields = []
    search_param = 'q'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get(self.search_param)
        
        if search_query and self.search_fields:
            from django.db.models import Q
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f'{field}__icontains': search_query})
            queryset = queryset.filter(query)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get(self.search_param, '')
        return context


class BreadcrumbMixin:
    """
    Миксин для хлебных крошек
    """
    breadcrumbs = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self):
        """
        Возвращает список хлебных крошек
        Каждый элемент: {'title': 'Название', 'url': 'URL'}
        """
        breadcrumbs = [
            {'title': 'Дашборд', 'url': reverse_lazy('dashboard:index')}
        ]
        breadcrumbs.extend(self.breadcrumbs)
        return breadcrumbs


class MenuRestaurantMixin(RestaurantOwnerMixin, FormValidationMixin, 
                         SearchMixin, PaginationMixin, BreadcrumbMixin):
    """
    Комбинированный миксин для меню ресторана
    """
    pass


class OrderRestaurantMixin(RestaurantOwnerMixin, FormValidationMixin, 
                          SearchMixin, PaginationMixin, BreadcrumbMixin):
    """
    Комбинированный миксин для заказов ресторана
    """
    pass 