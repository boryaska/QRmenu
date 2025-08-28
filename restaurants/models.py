import uuid
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, DecimalValidator
from core.models import TimeStampedModel
from core.utils import generate_restaurant_qr_data, UniqueFilenameStorage


class RestaurantProfile(TimeStampedModel):
    """
    Профиль ресторана с настройками и QR-данными
    """
    CURRENCY_CHOICES = [
        ('RUB', '₽ Рубль'),
        ('USD', '$ Доллар'),
        ('EUR', '€ Евро'),
        ('KZT', '₸ Тенге'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='restaurantprofile',
        verbose_name="Пользователь"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Название ресторана",
        help_text="Название вашего ресторана"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Краткое описание ресторана"
    )
    
    address = models.TextField(
        verbose_name="Адрес",
        help_text="Полный адрес ресторана"
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name="Телефон",
        help_text="Контактный телефон ресторана"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Email",
        help_text="Контактный email ресторана"
    )
    
    website = models.URLField(
        blank=True,
        verbose_name="Сайт",
        help_text="Официальный сайт ресторана"
    )
    
    logo = models.ImageField(
        upload_to='restaurants/logos/',
        blank=True,
        null=True,
        max_length=255,
        storage=UniqueFilenameStorage(),
        verbose_name="Логотип",
        help_text="Логотип ресторана для отображения в меню"
    )
    
    # Настройки ресторана
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='RUB',
        verbose_name="Валюта",
        help_text="Валюта для отображения цен"
    )
    
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[DecimalValidator(max_digits=5, decimal_places=2)],
        verbose_name="Налог (%)",
        help_text="Ставка налога в процентах (например, 10.00 для 10%)"
    )
    
    table_prefix = models.CharField(
        max_length=10,
        default="Стол",
        verbose_name="Префикс столов",
        help_text="Префикс для номеров столов (например: 'Стол', 'Table')"
    )
    
    service_charge = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[DecimalValidator(max_digits=5, decimal_places=2)],
        verbose_name="Сервисный сбор (%)",
        help_text="Сервисный сбор в процентах"
    )
    
    # QR-код данные
    qr_data = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="QR данные",
        help_text="Уникальный идентификатор для QR-кода"
    )
    
    qr_code = models.ImageField(
        upload_to='restaurants/qr_codes/',
        blank=True,
        null=True,
        max_length=255,
        storage=UniqueFilenameStorage(),
        verbose_name="QR-код",
        help_text="Сгенерированный QR-код для меню"
    )
    
    # Настройки работы
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Доступен ли ресторан для заказов"
    )
    
    working_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Часы работы",
        help_text="Расписание работы ресторана в формате JSON"
    )
    
    # SEO и дополнительная информация
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="SEO заголовок"
    )
    
    meta_description = models.TextField(
        blank=True,
        verbose_name="SEO описание"
    )

    class Meta:
        verbose_name = "Профиль ресторана"
        verbose_name_plural = "Профили ресторанов"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def save(self, *args, **kwargs):
        """
        Автоматически генерируем QR-данные при создании
        """
        if not self.qr_data:
            self.qr_data = generate_restaurant_qr_data()
        super().save(*args, **kwargs)

    def get_menu_url(self):
        """
        Возвращает полный URL для публичного меню
        """
        from django.conf import settings
        base_url = f"http://{settings.SITE_DOMAIN}" if settings.SITE_DOMAIN else "http://localhost:8000"
        return f"{base_url}/m/{self.qr_data}/"

    def get_currency_symbol(self):
        """
        Возвращает символ валюты
        """
        currency_symbols = {
            'RUB': '₽',
            'USD': '$',
            'EUR': '€',
            'KZT': '₸',
        }
        return currency_symbols.get(self.currency, '₽')

    def format_price(self, price):
        """
        Форматирует цену с валютой
        """
        return f"{price:.2f} {self.get_currency_symbol()}"

    def calculate_total_with_taxes(self, subtotal):
        """
        Рассчитывает общую сумму с налогами и сервисным сбором
        """
        tax_amount = subtotal * (self.tax_rate / 100)
        service_amount = subtotal * (self.service_charge / 100)
        return subtotal + tax_amount + service_amount

    def get_active_categories_count(self):
        """
        Возвращает количество активных категорий меню
        """
        return self.categories.filter(is_active=True).count()

    def get_active_dishes_count(self):
        """
        Возвращает количество активных блюд в меню
        """
        return self.dishes.filter(is_available=True).count()


class RestaurantSettings(TimeStampedModel):
    """
    Дополнительные настройки ресторана
    """
    restaurant = models.OneToOneField(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Ресторан"
    )
    
    # Настройки заказов
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Минимальная сумма заказа"
    )
    
    max_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=999999.99,
        verbose_name="Максимальная сумма заказа"
    )
    
    order_timeout_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="Таймаут заказа (мин)",
        help_text="Время в минутах, после которого заказ автоматически отменяется"
    )
    
    # Уведомления
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Email уведомления"
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name="SMS уведомления"
    )
    
    # Интеграции
    payment_gateway = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Платежный шлюз",
        help_text="Настройки платежной системы"
    )
    
    analytics_code = models.TextField(
        blank=True,
        verbose_name="Код аналитики",
        help_text="Google Analytics или другой код аналитики"
    )

    class Meta:
        verbose_name = "Настройки ресторана"
        verbose_name_plural = "Настройки ресторанов"

    def __str__(self):
        return f"Настройки для {self.restaurant.name}"
