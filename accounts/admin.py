from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Админка для кастомной модели пользователя
    """
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'is_active', 'date_joined', 'has_restaurant')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name')}),
        ('Разрешения', {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')

    def has_restaurant(self, obj):
        """
        Показывает, есть ли у пользователя профиль ресторана
        """
        has_profile = hasattr(obj, 'restaurantprofile')
        if has_profile:
            return format_html(
                '<span style="color: green;">✓ Да</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Нет</span>'
        )
    
    has_restaurant.short_description = 'Есть ресторан'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Админка для токенов сброса пароля
    """
    list_display = ('user', 'token_short', 'is_used', 'is_expired_now', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    def token_short(self, obj):
        """
        Показывает сокращенную версию токена
        """
        return f"{obj.token[:10]}..." if len(obj.token) > 10 else obj.token
    
    token_short.short_description = 'Токен'

    def is_expired_now(self, obj):
        """
        Показывает, истек ли токен
        """
        if obj.is_expired():
            return format_html(
                '<span style="color: red;">✗ Истек</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Действителен</span>'
        )
    
    is_expired_now.short_description = 'Статус'
