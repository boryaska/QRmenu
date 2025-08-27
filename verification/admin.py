from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import RestaurantVerification


@admin.register(RestaurantVerification)
class RestaurantVerificationAdmin(admin.ModelAdmin):
    """
    Админка для управления заявками на верификацию ресторанов
    """
    list_display = (
        'restaurant_name',
        'user_info',
        'status_colored',
        'phone',
        'submitted_at',
        'reviewed_at',
        'has_document',
        'is_updated_after_approval',
        'actions_buttons'
    )
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('restaurant_name', 'user__email', 'user__first_name', 'user__last_name', 'phone', 'address')
    readonly_fields = ('submitted_at', 'reviewed_at', 'user', 'restaurant_name', 'address', 'phone', 'email', 'description')
    ordering = ('-submitted_at',)
    actions = ['approve_applications', 'reject_applications', 'request_changes']

    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('user', 'user_info_display'),
            'classes': ('collapse',)
        }),
        ('Информация о ресторане', {
            'fields': ('restaurant_name', 'description', 'address', 'phone', 'email')
        }),
        ('Документы', {
            'fields': ('document_file', 'document_preview'),
            'classes': ('collapse',)
        }),
        ('Статус и комментарии', {
            'fields': ('status', 'admin_comment', 'submitted_at', 'reviewed_at')
        })
    )

    def user_info(self, obj):
        """Показывает информацию о пользователе"""
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.email,
            obj.user.email
        )
    user_info.short_description = 'Пользователь'

    def user_info_display(self, obj):
        """Показывает информацию о пользователе в форме редактирования"""
        return format_html(
            '<strong>{}</strong><br/><small>{}</small><br/>Дата регистрации: {}',
            obj.user.get_full_name() or obj.user.email,
            obj.user.email,
            obj.user.created_at.strftime('%d.%m.%Y %H:%M')
        )
    user_info_display.short_description = 'Информация о пользователе'

    def status_colored(self, obj):
        """Показывает статус с цветовой индикацией"""
        colors = {
            'pending': '#f59e0b',  # amber
            'approved': '#10b981',  # emerald
            'rejected': '#ef4444',  # red
            'requires_changes': '#f97316',  # orange
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Статус'
    status_colored.admin_order_field = 'status'

    def has_document(self, obj):
        """Показывает, загружен ли документ"""
        if obj.document_file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #10b981;">📎 Просмотреть</a>',
                obj.document_file.url
            )
        return format_html('<span style="color: #ef4444;">Нет документа</span>')
    has_document.short_description = 'Документ'

    def document_preview(self, obj):
        """Показывает превью документа в форме редактирования"""
        if obj.document_file:
            return format_html(
                '<a href="{}" target="_blank">📎 Открыть документ</a>',
                obj.document_file.url
            )
        return "Документ не загружен"
    document_preview.short_description = 'Превью документа'

    def is_updated_after_approval(self, obj):
        """Показывает, была ли заявка изменена после одобрения"""
        if (obj.status == 'pending' and
            obj.admin_comment and
            'обновлена пользователем' in obj.admin_comment):
            return format_html(
                '<span style="color: #f97316; font-weight: bold;">🔄 Изменена</span>'
            )
        return format_html('<span style="color: #6b7280;">—</span>')
    is_updated_after_approval.short_description = 'Изменена'

    def actions_buttons(self, obj):
        """Показывает кнопки действий"""
        if obj.status == 'pending':
            return format_html(
                '<a href="{}" class="button" style="background: #10b981; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none; margin-right: 5px;">✓ Одобрить</a>'
                '<a href="{}" class="button" style="background: #f97316; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none; margin-right: 5px;">⚠ Изменения</a>'
                '<a href="{}" class="button" style="background: #ef4444; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none;">✗ Отклонить</a>',
                reverse('admin:verification_restaurantverification_change', args=[obj.pk]) + '?action=approve',
                reverse('admin:verification_restaurantverification_change', args=[obj.pk]) + '?action=request_changes',
                reverse('admin:verification_restaurantverification_change', args=[obj.pk]) + '?action=reject'
            )
        return format_html('<span style="color: #6b7280;">Действия недоступны</span>')
    actions_buttons.short_description = 'Действия'

    def approve_applications(self, request, queryset):
        """Массовое одобрение заявок"""
        updated = 0
        for verification in queryset.filter(status='pending'):
            try:
                restaurant = verification.approve('Заявка одобрена через массовое действие')
                updated += 1
                self.message_user(
                    request,
                    f'Заявка для "{verification.restaurant_name}" одобрена. Создан ресторан "{restaurant.name}".',
                    level='SUCCESS'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Ошибка при одобрении заявки для "{verification.restaurant_name}": {e}',
                    level='ERROR'
                )

        self.message_user(request, f'Обработано {updated} заявок.')
    approve_applications.short_description = 'Одобрить выбранные заявки'

    def reject_applications(self, request, queryset):
        """Массовое отклонение заявок"""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_at=timezone.now(),
            admin_comment='Заявка отклонена через массовое действие'
        )
        self.message_user(request, f'Отклонено {updated} заявок.')
    reject_applications.short_description = 'Отклонить выбранные заявки'

    def request_changes(self, request, queryset):
        """Массовый запрос изменений"""
        updated = queryset.filter(status='pending').update(
            status='requires_changes',
            admin_comment='Необходимо внести изменения. Свяжитесь с администрацией для уточнения деталей.'
        )
        self.message_user(request, f'Отправлен запрос на изменения для {updated} заявок.')
    request_changes.short_description = 'Запросить изменения для выбранных заявок'

    def save_model(self, request, obj, form, change):
        """Дополнительная логика при сохранении"""
        if change and obj.status != form.initial.get('status'):
            # Статус изменился
            obj.reviewed_at = timezone.now()

            if obj.status == 'approved':
                try:
                    restaurant = obj.approve(obj.admin_comment)
                    self.message_user(
                        request,
                        f'Заявка одобрена! Создан ресторан "{restaurant.name}".',
                        level='SUCCESS'
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f'Ошибка при создании ресторана: {e}',
                        level='ERROR'
                    )
            elif obj.status == 'rejected':
                obj.reject(obj.admin_comment)
                self.message_user(request, 'Заявка отклонена.', level='WARNING')
            elif obj.status == 'requires_changes':
                obj.request_changes(obj.admin_comment)
                self.message_user(request, 'Отправлен запрос на внесение изменений.', level='INFO')

        super().save_model(request, obj, form, change)
