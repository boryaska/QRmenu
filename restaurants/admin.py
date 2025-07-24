from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RestaurantProfile, RestaurantSettings


class RestaurantSettingsInline(admin.StackedInline):
    """
    Инлайн для настроек ресторана
    """
    model = RestaurantSettings
    extra = 0
    fields = (
        ('min_order_amount', 'max_order_amount'),
        'order_timeout_minutes',
        ('email_notifications', 'sms_notifications'),
        'payment_gateway',
        'analytics_code',
    )


@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    """
    Админка для профилей ресторанов
    """
    list_display = (
        'name', 
        'user_email', 
        'phone', 
        'currency', 
        'is_active', 
        'dishes_count',
        'categories_count',
        'qr_code_preview',
        'created_at'
    )
    list_filter = ('is_active', 'currency', 'created_at')
    search_fields = ('name', 'user__email', 'phone', 'address')
    readonly_fields = ('qr_data', 'created_at', 'updated_at', 'qr_code_preview', 'menu_url_link')
    ordering = ('-created_at',)
    inlines = [RestaurantSettingsInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'name', 'description', 'logo')
        }),
        ('Контактные данные', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Настройки меню', {
            'fields': ('currency', 'tax_rate', 'service_charge', 'table_prefix', 'is_active')
        }),
        ('QR-код и ссылки', {
            'fields': ('qr_data', 'qr_code', 'qr_code_preview', 'menu_url_link'),
            'classes': ('collapse',)
        }),
        ('Расписание работы', {
            'fields': ('working_hours',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def user_email(self, obj):
        """
        Показывает email пользователя
        """
        return obj.user.email
    user_email.short_description = 'Email пользователя'

    def dishes_count(self, obj):
        """
        Показывает количество блюд
        """
        try:
            count = obj.get_active_dishes_count()
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        except:
            return '-'
    dishes_count.short_description = 'Блюда'

    def categories_count(self, obj):
        """
        Показывает количество категорий
        """
        try:
            count = obj.get_active_categories_count()
            return format_html(
                '<span style="color: blue; font-weight: bold;">{}</span>',
                count
            )
        except:
            return '-'
    categories_count.short_description = 'Категории'

    def qr_code_preview(self, obj):
        """
        Показывает превью QR-кода
        """
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.qr_code.url
            )
        return "Нет QR-кода"
    qr_code_preview.short_description = 'QR-код'

    def menu_url_link(self, obj):
        """
        Показывает ссылку на публичное меню
        """
        if obj.qr_data:
            url = obj.get_menu_url()
            return format_html(
                '<a href="{}" target="_blank" style="color: #007cba; text-decoration: none;">'
                'Открыть меню ↗'
                '</a>',
                url
            )
        return "Нет ссылки"
    menu_url_link.short_description = 'Ссылка на меню'

    def save_model(self, request, obj, form, change):
        """
        Дополнительная логика при сохранении
        """
        super().save_model(request, obj, form, change)
        
        # Создаем настройки ресторана, если их нет
        if not hasattr(obj, 'settings'):
            RestaurantSettings.objects.create(restaurant=obj)

    actions = ['generate_qr_codes', 'activate_restaurants', 'deactivate_restaurants']

    def generate_qr_codes(self, request, queryset):
        """
        Генерирует QR-коды для выбранных ресторанов
        """
        from core.utils import generate_qr_code
        
        updated = 0
        for restaurant in queryset:
            if restaurant.qr_data:
                menu_url = restaurant.get_menu_url()
                qr_file = generate_qr_code(menu_url)
                restaurant.qr_code.save(
                    f'qr_{restaurant.qr_data}.png',
                    qr_file,
                    save=True
                )
                updated += 1
        
        self.message_user(
            request,
            f'QR-коды сгенерированы для {updated} ресторанов.'
        )
    generate_qr_codes.short_description = 'Сгенерировать QR-коды'

    def activate_restaurants(self, request, queryset):
        """
        Активирует выбранные рестораны
        """
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} ресторанов активированы.'
        )
    activate_restaurants.short_description = 'Активировать рестораны'

    def deactivate_restaurants(self, request, queryset):
        """
        Деактивирует выбранные рестораны
        """
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} ресторанов деактивированы.'
        )
    deactivate_restaurants.short_description = 'Деактивировать рестораны'


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    """
    Админка для настроек ресторанов
    """
    list_display = (
        'restaurant', 
        'min_order_amount_formatted', 
        'max_order_amount_formatted',
        'order_timeout_minutes',
        'email_notifications',
        'sms_notifications'
    )
    list_filter = ('email_notifications', 'sms_notifications', 'created_at')
    search_fields = ('restaurant__name', 'restaurant__user__email')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Настройки заказов', {
            'fields': ('restaurant', 'min_order_amount', 'max_order_amount', 'order_timeout_minutes')
        }),
        ('Уведомления', {
            'fields': ('email_notifications', 'sms_notifications')
        }),
        ('Интеграции', {
            'fields': ('payment_gateway', 'analytics_code'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def min_order_amount_formatted(self, obj):
        """
        Форматированная минимальная сумма заказа
        """
        return obj.restaurant.format_price(obj.min_order_amount)
    min_order_amount_formatted.short_description = 'Мин. сумма'

    def max_order_amount_formatted(self, obj):
        """
        Форматированная максимальная сумма заказа
        """
        return obj.restaurant.format_price(obj.max_order_amount)
    max_order_amount_formatted.short_description = 'Макс. сумма'
