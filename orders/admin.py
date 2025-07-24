from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils import timezone

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Инлайн для позиций заказа
    """
    model = OrderItem
    extra = 0
    fields = ['dish', 'quantity', 'unit_price', 'special_requests']
    readonly_fields = ['unit_price']
    
    def get_queryset(self, request):
        """
        Оптимизируем запросы для инлайна
        """
        return super().get_queryset(request).select_related('dish')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Админка для заказов
    """
    list_display = [
        'order_number', 'restaurant', 'customer_info', 'table_number',
        'items_count', 'total_amount_display', 'status_display', 
        'payment_status', 'created_at'
    ]
    list_filter = [
        'status', 'is_paid', 'payment_method', 'restaurant', 
        'created_at', 'confirmed_at'
    ]
    search_fields = [
        'order_number', 'customer_name', 'customer_phone', 
        'customer_email', 'table_number', 'restaurant__name'
    ]
    list_editable = []
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Информация о заказе', {
            'fields': ['order_number', 'restaurant', 'status', 'qr_data']
        }),
        ('Клиент', {
            'fields': ['customer_name', 'customer_phone', 'customer_email', 'table_number']
        }),
        ('Суммы', {
            'fields': ['subtotal', 'tax_amount', 'service_amount', 'total_amount']
        }),
        ('Оплата', {
            'fields': ['payment_method', 'is_paid', 'paid_at']
        }),
        ('Дополнительная информация', {
            'fields': ['special_requests', 'estimated_ready_time'],
            'classes': ['collapse']
        }),
        ('Техническая информация', {
            'fields': ['customer_ip', 'user_agent'],
            'classes': ['collapse']
        }),
        ('Временные метки', {
            'fields': ['created_at', 'confirmed_at', 'completed_at', 'cancelled_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = [
        'order_number', 'qr_data', 'customer_ip', 'user_agent',
        'created_at', 'confirmed_at', 'completed_at', 'cancelled_at',
        'subtotal', 'tax_amount', 'service_amount', 'total_amount'
    ]
    
    inlines = [OrderItemInline]
    actions = ['mark_as_confirmed', 'mark_as_preparing', 'mark_as_ready', 'mark_as_completed']

    def get_queryset(self, request):
        """
        Фильтруем заказы по ресторану пользователя
        """
        queryset = super().get_queryset(request).select_related('restaurant').annotate(
            items_count=Count('items')
        )
        
        if request.user.is_superuser:
            return queryset
        
        if hasattr(request.user, 'restaurantprofile'):
            return queryset.filter(restaurant=request.user.restaurantprofile)
        
        return queryset.none()

    def customer_info(self, obj):
        """
        Информация о клиенте
        """
        info_parts = []
        if obj.customer_name:
            info_parts.append(obj.customer_name)
        if obj.customer_phone:
            info_parts.append(obj.customer_phone)
        
        return ' | '.join(info_parts) if info_parts else 'Анонимный заказ'
    customer_info.short_description = 'Клиент'

    def items_count(self, obj):
        """
        Количество позиций в заказе
        """
        return obj.items_count if hasattr(obj, 'items_count') else obj.get_items_count()
    items_count.short_description = 'Позиций'
    items_count.admin_order_field = 'items_count'

    def total_amount_display(self, obj):
        """
        Форматированная общая сумма
        """
        return f"{obj.total_amount:.2f} {obj.restaurant.get_currency_symbol()}"
    total_amount_display.short_description = 'Сумма'
    total_amount_display.admin_order_field = 'total_amount'

    def status_display(self, obj):
        """
        Статус с цветовой индикацией
        """
        status_colors = {
            'pending': '#ffc107',      # желтый
            'confirmed': '#17a2b8',    # голубой
            'preparing': '#fd7e14',    # оранжевый
            'ready': '#28a745',        # зеленый
            'completed': '#6c757d',    # серый
            'cancelled': '#dc3545',    # красный
        }
        
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'

    def payment_status(self, obj):
        """
        Статус оплаты
        """
        if obj.is_paid:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Оплачен</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Не оплачен</span>'
            )
    payment_status.short_description = 'Оплата'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор ресторана
        """
        if db_field.name == 'restaurant' and not request.user.is_superuser:
            if hasattr(request.user, 'restaurantprofile'):
                kwargs['queryset'] = kwargs['queryset'].filter(
                    id=request.user.restaurantprofile.id
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Групповые действия
    def mark_as_confirmed(self, request, queryset):
        """
        Подтвердить заказы
        """
        count = 0
        for order in queryset.filter(status='pending'):
            order.update_status('confirmed')
            count += 1
        
        self.message_user(request, f'Подтверждено заказов: {count}')
    mark_as_confirmed.short_description = 'Подтвердить выбранные заказы'

    def mark_as_preparing(self, request, queryset):
        """
        Отметить заказы как готовящиеся
        """
        count = 0
        for order in queryset.filter(status='confirmed'):
            order.update_status('preparing')
            count += 1
        
        self.message_user(request, f'Заказов в работе: {count}')
    mark_as_preparing.short_description = 'Отметить как готовящиеся'

    def mark_as_ready(self, request, queryset):
        """
        Отметить заказы как готовые
        """
        count = 0
        for order in queryset.filter(status='preparing'):
            order.update_status('ready')
            count += 1
        
        self.message_user(request, f'Готовых заказов: {count}')
    mark_as_ready.short_description = 'Отметить как готовые'

    def mark_as_completed(self, request, queryset):
        """
        Завершить заказы
        """
        count = 0
        for order in queryset.filter(status='ready'):
            order.update_status('completed')
            count += 1
        
        self.message_user(request, f'Завершенных заказов: {count}')
    mark_as_completed.short_description = 'Завершить заказы'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Админка для позиций заказов
    """
    list_display = [
        'order_link', 'dish', 'quantity', 'unit_price_display', 
        'total_price_display', 'has_options', 'special_requests_short'
    ]
    list_filter = ['order__status', 'order__restaurant', 'dish__category']
    search_fields = [
        'order__order_number', 'dish__name', 'special_requests',
        'order__customer_name', 'order__restaurant__name'
    ]
    ordering = ['-order__created_at', 'id']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['order', 'dish', 'quantity', 'unit_price']
        }),
        ('Опции и пожелания', {
            'fields': ['selected_options', 'special_requests']
        }),
    ]
    
    readonly_fields = ['unit_price']

    def get_queryset(self, request):
        """
        Фильтруем позиции заказов по ресторану пользователя
        """
        queryset = super().get_queryset(request).select_related(
            'order__restaurant', 'dish'
        )
        
        if request.user.is_superuser:
            return queryset
        
        if hasattr(request.user, 'restaurantprofile'):
            return queryset.filter(order__restaurant=request.user.restaurantprofile)
        
        return queryset.none()

    def order_link(self, obj):
        """
        Ссылка на заказ
        """
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Заказ'

    def unit_price_display(self, obj):
        """
        Форматированная цена за единицу
        """
        return f"{obj.unit_price:.2f} {obj.order.restaurant.get_currency_symbol()}"
    unit_price_display.short_description = 'Цена за ед.'

    def total_price_display(self, obj):
        """
        Общая стоимость позиции
        """
        total = obj.get_total_price()
        return f"{total:.2f} {obj.order.restaurant.get_currency_symbol()}"
    total_price_display.short_description = 'Общая стоимость'

    def has_options(self, obj):
        """
        Есть ли выбранные опции
        """
        if obj.selected_options:
            return format_html('<span style="color: #28a745;">✓ Есть</span>')
        return '—'
    has_options.short_description = 'Опции'

    def special_requests_short(self, obj):
        """
        Сокращенные особые пожелания
        """
        if obj.special_requests:
            return obj.special_requests[:50] + ('...' if len(obj.special_requests) > 50 else '')
        return '—'
    special_requests_short.short_description = 'Пожелания'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем выбор заказов и блюд
        """
        if not request.user.is_superuser and hasattr(request.user, 'restaurantprofile'):
            restaurant = request.user.restaurantprofile
            
            if db_field.name == 'order':
                kwargs['queryset'] = kwargs['queryset'].filter(restaurant=restaurant)
            elif db_field.name == 'dish':
                kwargs['queryset'] = kwargs['queryset'].filter(restaurant=restaurant)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
