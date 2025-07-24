from rest_framework import serializers
from .models import RestaurantProfile, RestaurantSettings


class RestaurantProfileSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор профиля ресторана
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    menu_url = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()
    active_dishes_count = serializers.SerializerMethodField()
    active_categories_count = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = RestaurantProfile
        fields = [
            'id', 'user_email', 'name', 'description', 'address', 'phone', 
            'email', 'website', 'logo', 'currency', 'currency_symbol',
            'tax_rate', 'service_charge', 'table_prefix', 'qr_data', 
            'qr_code_url', 'is_active', 'working_hours', 'meta_title', 
            'meta_description', 'menu_url', 'active_dishes_count', 
            'active_categories_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'qr_data', 'created_at', 'updated_at'
        ]

    def get_menu_url(self, obj):
        """
        Возвращает URL публичного меню
        """
        return obj.get_menu_url()

    def get_currency_symbol(self, obj):
        """
        Возвращает символ валюты
        """
        return obj.get_currency_symbol()

    def get_active_dishes_count(self, obj):
        """
        Возвращает количество активных блюд
        """
        try:
            return obj.get_active_dishes_count()
        except:
            return 0

    def get_active_categories_count(self, obj):
        """
        Возвращает количество активных категорий
        """
        try:
            return obj.get_active_categories_count()
        except:
            return 0

    def get_qr_code_url(self, obj):
        """
        Возвращает URL QR-кода
        """
        if obj.qr_code:
            return obj.qr_code.url
        return None


class RestaurantProfileCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания профиля ресторана
    """
    class Meta:
        model = RestaurantProfile
        fields = [
            'name', 'description', 'address', 'phone', 'email', 'website', 
            'logo', 'currency', 'tax_rate', 'service_charge', 'table_prefix'
        ]

    def validate_name(self, value):
        """
        Проверяем название ресторана
        """
        if not value.strip():
            raise serializers.ValidationError("Название ресторана не может быть пустым")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Название ресторана должно содержать минимум 2 символа")
        
        return value.strip()

    def validate_address(self, value):
        """
        Проверяем адрес
        """
        if not value.strip():
            raise serializers.ValidationError("Адрес не может быть пустым")
        return value.strip()

    def validate_phone(self, value):
        """
        Проверяем телефон
        """
        if not value.strip():
            raise serializers.ValidationError("Телефон не может быть пустым")
        return value.strip()

    def validate_tax_rate(self, value):
        """
        Проверяем налоговую ставку
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Налоговая ставка должна быть от 0 до 100%")
        return value

    def validate_service_charge(self, value):
        """
        Проверяем сервисный сбор
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Сервисный сбор должен быть от 0 до 100%")
        return value


class RestaurantProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля ресторана
    """
    class Meta:
        model = RestaurantProfile
        fields = [
            'name', 'description', 'address', 'phone', 'email', 'website', 
            'logo', 'currency', 'tax_rate', 'service_charge', 'table_prefix', 
            'is_active', 'working_hours', 'meta_title', 'meta_description'
        ]

    def validate_name(self, value):
        """
        Проверяем название ресторана
        """
        if value and not value.strip():
            raise serializers.ValidationError("Название ресторана не может быть пустым")
        
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("Название ресторана должно содержать минимум 2 символа")
        
        return value.strip() if value else value

    def validate_tax_rate(self, value):
        """
        Проверяем налоговую ставку
        """
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Налоговая ставка должна быть от 0 до 100%")
        return value

    def validate_service_charge(self, value):
        """
        Проверяем сервисный сбор
        """
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Сервисный сбор должен быть от 0 до 100%")
        return value


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    """
    Сериализатор настроек ресторана
    """
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = RestaurantSettings
        fields = [
            'id', 'restaurant_name', 'min_order_amount', 'max_order_amount',
            'order_timeout_minutes', 'email_notifications', 'sms_notifications',
            'payment_gateway', 'analytics_code', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'restaurant_name', 'created_at', 'updated_at']

    def validate_min_order_amount(self, value):
        """
        Проверяем минимальную сумму заказа
        """
        if value < 0:
            raise serializers.ValidationError("Минимальная сумма заказа не может быть отрицательной")
        return value

    def validate_max_order_amount(self, value):
        """
        Проверяем максимальную сумму заказа
        """
        if value <= 0:
            raise serializers.ValidationError("Максимальная сумма заказа должна быть больше 0")
        return value

    def validate_order_timeout_minutes(self, value):
        """
        Проверяем таймаут заказа
        """
        if value < 1 or value > 1440:  # от 1 минуты до 24 часов
            raise serializers.ValidationError("Таймаут заказа должен быть от 1 до 1440 минут")
        return value

    def validate(self, attrs):
        """
        Проверяем соотношение мин/макс сумм заказа
        """
        min_amount = attrs.get('min_order_amount')
        max_amount = attrs.get('max_order_amount')
        
        # Если обновляем частично, получаем существующие значения
        if self.instance:
            if min_amount is None:
                min_amount = self.instance.min_order_amount
            if max_amount is None:
                max_amount = self.instance.max_order_amount
        
        if min_amount is not None and max_amount is not None:
            if min_amount >= max_amount:
                raise serializers.ValidationError(
                    "Минимальная сумма заказа должна быть меньше максимальной"
                )
        
        return attrs


class PublicRestaurantSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор ресторана (для клиентов)
    """
    currency_symbol = serializers.SerializerMethodField()
    formatted_phone = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = RestaurantProfile
        fields = [
            'name', 'description', 'address', 'formatted_phone', 'email', 
            'website', 'logo_url', 'currency', 'currency_symbol', 
            'table_prefix', 'working_hours'
        ]

    def get_currency_symbol(self, obj):
        """
        Возвращает символ валюты
        """
        return obj.get_currency_symbol()

    def get_formatted_phone(self, obj):
        """
        Форматирует телефон для отображения
        """
        return obj.phone

    def get_logo_url(self, obj):
        """
        Возвращает URL логотипа
        """
        if obj.logo:
            return obj.logo.url
        return None


class RestaurantBriefSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор ресторана (для списков)
    """
    currency_symbol = serializers.SerializerMethodField()

    class Meta:
        model = RestaurantProfile
        fields = [
            'id', 'name', 'address', 'phone', 'currency', 
            'currency_symbol', 'is_active'
        ]

    def get_currency_symbol(self, obj):
        """
        Возвращает символ валюты
        """
        return obj.get_currency_symbol()


class QRCodeInfoSerializer(serializers.Serializer):
    """
    Сериализатор информации о QR-коде
    """
    qr_data = serializers.CharField(read_only=True)
    qr_code_url = serializers.URLField(read_only=True, allow_null=True)
    menu_url = serializers.URLField(read_only=True)
    has_qr_code = serializers.BooleanField(read_only=True) 