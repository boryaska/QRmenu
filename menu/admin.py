from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count

from .models import Category, Dish, DishOption, DishIngredient


class DishOptionInline(admin.TabularInline):
    """
    Инлайн для опций блюда
    """
    model = DishOption
    extra = 0
    fields = ['name', 'price_modifier', 'is_required', 'is_available', 'sort_order']
    ordering = ['sort_order', 'name']


class DishIngredientInline(admin.TabularInline):
    """
    Инлайн для ингредиентов блюда
    """
    model = DishIngredient
    extra = 0
    fields = ['name', 'quantity', 'is_allergen', 'can_exclude']
    ordering = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Админка для категорий меню
    """
    list_display = [
        'name', 'restaurant', 'dishes_count', 'sort_order', 
        'is_active', 'image_preview', 'created_at'
    ]
    list_filter = ['restaurant', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'restaurant__name']
    list_editable = ['sort_order', 'is_active']
    ordering = ['restaurant__name', 'sort_order', 'name']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['restaurant', 'name', 'description']
        }),
        ('Изображение', {
            'fields': ['image'],
            'description': 'Изображение категории (рекомендуемый размер: 400x300px)'
        }),
        ('Настройки отображения', {
            'fields': ['sort_order', 'is_active']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        """
        Фильтруем категории по ресторану пользователя для обычных пользователей
        """
        queryset = super().get_queryset(request)
        
        # Для суперпользователей показываем все
        if request.user.is_superuser:
            return queryset.annotate(dishes_count=Count('dishes'))
        
        # Для владельцев ресторанов показываем только их категории
        if hasattr(request.user, 'restaurantprofile'):
            return queryset.filter(
                restaurant=request.user.restaurantprofile
            ).annotate(dishes_count=Count('dishes'))
        
        # Для остальных - пустой queryset
        return queryset.none()

    def dishes_count(self, obj):
        """
        Количество блюд в категории
        """
        return obj.dishes_count if hasattr(obj, 'dishes_count') else obj.dishes.count()
    dishes_count.short_description = 'Блюд'
    dishes_count.admin_order_field = 'dishes_count'

    def image_preview(self, obj):
        """
        Превью изображения категории
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Превью'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор ресторана для обычных пользователей
        """
        if db_field.name == 'restaurant' and not request.user.is_superuser:
            if hasattr(request.user, 'restaurantprofile'):
                kwargs['queryset'] = kwargs['queryset'].filter(
                    id=request.user.restaurantprofile.id
                )
                kwargs['initial'] = request.user.restaurantprofile.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    """
    Админка для блюд
    """
    list_display = [
        'name', 'category', 'restaurant', 'price_display', 
        'status_badges', 'sort_order', 'is_available', 
        'image_preview', 'created_at'
    ]
    list_filter = [
        'restaurant', 'category', 'is_available', 'is_popular', 
        'is_new', 'is_vegetarian', 'is_vegan', 'is_spicy', 'created_at'
    ]
    search_fields = ['name', 'description', 'ingredients', 'restaurant__name']
    list_editable = ['sort_order', 'is_available']
    ordering = ['restaurant__name', 'category__sort_order', 'sort_order', 'name']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['restaurant', 'category', 'name', 'description', 'ingredients']
        }),
        ('Цена и изображение', {
            'fields': ['price', 'image']
        }),
        ('Пищевая ценность', {
            'fields': ['calories', 'proteins', 'fats', 'carbohydrates'],
            'classes': ['collapse']
        }),
        ('Дополнительная информация', {
            'fields': ['weight', 'cooking_time'],
            'classes': ['collapse']
        }),
        ('Метки и характеристики', {
            'fields': [
                'is_popular', 'is_new', 'is_spicy', 
                'is_vegetarian', 'is_vegan'
            ]
        }),
        ('Настройки отображения', {
            'fields': ['sort_order', 'is_available']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DishOptionInline, DishIngredientInline]

    def get_queryset(self, request):
        """
        Фильтруем блюда по ресторану пользователя
        """
        queryset = super().get_queryset(request).select_related(
            'restaurant', 'category'
        )
        
        if request.user.is_superuser:
            return queryset
        
        if hasattr(request.user, 'restaurantprofile'):
            return queryset.filter(restaurant=request.user.restaurantprofile)
        
        return queryset.none()

    def price_display(self, obj):
        """
        Форматированная цена
        """
        return obj.get_formatted_price()
    price_display.short_description = 'Цена'

    def status_badges(self, obj):
        """
        Отображение меток блюда
        """
        badges = []
        if obj.is_new:
            badges.append('<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Новинка</span>')
        if obj.is_popular:
            badges.append('<span style="background: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Популярное</span>')
        if obj.is_spicy:
            badges.append('<span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🌶️ Острое</span>')
        if obj.is_vegetarian:
            badges.append('<span style="background: #198754; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🥬 Вегетарианское</span>')
        if obj.is_vegan:
            badges.append('<span style="background: #20c997; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🌱 Веганское</span>')
        
        return mark_safe(' '.join(badges)) if badges else '—'
    status_badges.short_description = 'Метки'

    def image_preview(self, obj):
        """
        Превью изображения блюда
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Превью'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор ресторана и категорий
        """
        if not request.user.is_superuser and hasattr(request.user, 'restaurantprofile'):
            restaurant = request.user.restaurantprofile
            
            if db_field.name == 'restaurant':
                kwargs['queryset'] = kwargs['queryset'].filter(id=restaurant.id)
                kwargs['initial'] = restaurant.id
            elif db_field.name == 'category':
                kwargs['queryset'] = kwargs['queryset'].filter(restaurant=restaurant)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DishOption)
class DishOptionAdmin(admin.ModelAdmin):
    """
    Админка для опций блюд
    """
    list_display = [
        'name', 'dish', 'price_modifier_display', 
        'is_required', 'is_available', 'sort_order'
    ]
    list_filter = ['is_required', 'is_available', 'dish__restaurant']
    search_fields = ['name', 'dish__name', 'dish__restaurant__name']
    list_editable = ['is_required', 'is_available', 'sort_order']
    ordering = ['dish__restaurant__name', 'dish__name', 'sort_order']

    def get_queryset(self, request):
        """
        Фильтруем опции по ресторану пользователя
        """
        queryset = super().get_queryset(request).select_related(
            'dish__restaurant'
        )
        
        if request.user.is_superuser:
            return queryset
        
        if hasattr(request.user, 'restaurantprofile'):
            return queryset.filter(dish__restaurant=request.user.restaurantprofile)
        
        return queryset.none()

    def price_modifier_display(self, obj):
        """
        Форматированное изменение цены
        """
        if obj.price_modifier > 0:
            return f"+{obj.price_modifier} ₽"
        elif obj.price_modifier < 0:
            return f"{obj.price_modifier} ₽"
        else:
            return "Бесплатно"
    price_modifier_display.short_description = 'Изменение цены'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор блюд
        """
        if db_field.name == 'dish' and not request.user.is_superuser:
            if hasattr(request.user, 'restaurantprofile'):
                kwargs['queryset'] = kwargs['queryset'].filter(
                    restaurant=request.user.restaurantprofile
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DishIngredient)
class DishIngredientAdmin(admin.ModelAdmin):
    """
    Админка для ингредиентов блюд
    """
    list_display = [
        'name', 'dish', 'quantity', 'allergen_status', 'can_exclude'
    ]
    list_filter = ['is_allergen', 'can_exclude', 'dish__restaurant']
    search_fields = ['name', 'dish__name', 'dish__restaurant__name']
    list_editable = ['quantity', 'can_exclude']
    ordering = ['dish__restaurant__name', 'dish__name', 'name']

    def get_queryset(self, request):
        """
        Фильтруем ингредиенты по ресторану пользователя
        """
        queryset = super().get_queryset(request).select_related(
            'dish__restaurant'
        )
        
        if request.user.is_superuser:
            return queryset
        
        if hasattr(request.user, 'restaurantprofile'):
            return queryset.filter(dish__restaurant=request.user.restaurantprofile)
        
        return queryset.none()

    def allergen_status(self, obj):
        """
        Статус аллергена
        """
        if obj.is_allergen:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠️ Аллерген</span>'
            )
        return '—'
    allergen_status.short_description = 'Аллерген'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор блюд
        """
        if db_field.name == 'dish' and not request.user.is_superuser:
            if hasattr(request.user, 'restaurantprofile'):
                kwargs['queryset'] = kwargs['queryset'].filter(
                    restaurant=request.user.restaurantprofile
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
