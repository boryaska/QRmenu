from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import json

from core.models import TimeStampedModel
from core.utils import generate_order_number, calculate_order_total, get_client_ip
from restaurants.models import RestaurantProfile
from menu.models import Dish, DishOption


class Order(TimeStampedModel):
    """
    Заказ в ресторане
    """
    
    # Статусы заказа
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтвержден'),
        ('preparing', 'Готовится'),
        ('ready', 'Готов'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]
    
    # Способы оплаты
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличными'),
        ('card', 'Картой'),
        ('online', 'Онлайн'),
    ]
    
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Ресторан"
    )
    
    # Номер заказа
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Номер заказа",
        help_text="Автоматически генерируемый номер заказа"
    )
    
    # Информация о клиенте
    customer_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Имя клиента",
        help_text="Имя клиента (необязательно)"
    )
    
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон клиента",
        help_text="Контактный телефон клиента"
    )
    
    customer_email = models.EmailField(
        blank=True,
        verbose_name="Email клиента",
        help_text="Email клиента для уведомлений"
    )
    
    # Информация о столе/доставке
    table_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Номер стола",
        help_text="Номер стола в ресторане"
    )
    
    # Статус и время
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус заказа"
    )
    
    # Суммы заказа
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Сумма без налогов"
    )
    
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Сумма налога"
    )
    
    service_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Сервисный сбор"
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Общая сумма"
    )
    
    # Платеж
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        verbose_name="Способ оплаты"
    )
    
    is_paid = models.BooleanField(
        default=False,
        verbose_name="Оплачен",
        help_text="Оплачен ли заказ"
    )
    
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время оплаты"
    )
    
    # Дополнительная информация
    special_requests = models.TextField(
        blank=True,
        verbose_name="Особые пожелания",
        help_text="Комментарии клиента к заказу"
    )
    
    estimated_ready_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Ожидаемое время готовности"
    )
    
    # Техническая информация
    qr_data = models.CharField(
        max_length=100,
        verbose_name="QR данные",
        help_text="QR данные ресторана, через которые был сделан заказ"
    )
    
    customer_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP клиента"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Информация о браузере клиента"
    )
    
    # Временные метки
    confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время подтверждения"
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время выполнения"
    )
    
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время отмены"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['is_paid']),
        ]

    def __str__(self):
        return f"Заказ {self.order_number} - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        """
        Переопределяем сохранение для автоматической генерации номера заказа
        """
        if not self.order_number:
            self.order_number = generate_order_number()
        
        # Устанавливаем qr_data от ресторана
        if not self.qr_data and self.restaurant:
            self.qr_data = self.restaurant.qr_data
            
        super().save(*args, **kwargs)

    def clean(self):
        """
        Валидация заказа
        """
        super().clean()
        
        # Проверяем, что сумма заказа положительная
        if self.total_amount < 0:
            raise ValidationError('Общая сумма заказа не может быть отрицательной')

    def calculate_totals(self):
        """
        Пересчитывает суммы заказа на основе позиций
        """
        # Считаем subtotal из позиций заказа
        self.subtotal = sum(item.get_total_price() for item in self.items.all())
        
        # Применяем налоги и сборы ресторана
        calculation = calculate_order_total(
            self.subtotal,
            self.restaurant.tax_rate,
            self.restaurant.service_charge
        )
        
        self.tax_amount = calculation['tax_amount']
        self.service_amount = calculation['service_amount']
        self.total_amount = calculation['total']

    def get_items_count(self):
        """
        Возвращает общее количество позиций в заказе
        """
        return sum(item.quantity for item in self.items.all())

    def get_status_display_class(self):
        """
        Возвращает CSS класс для отображения статуса
        """
        status_classes = {
            'pending': 'status-pending',
            'confirmed': 'status-confirmed',
            'preparing': 'status-preparing',
            'ready': 'status-ready',
            'completed': 'status-completed',
            'cancelled': 'status-cancelled',
        }
        return status_classes.get(self.status, 'status-default')

    def can_cancel(self):
        """
        Проверяет, можно ли отменить заказ
        """
        return self.status in ['pending', 'confirmed']

    def can_modify(self):
        """
        Проверяет, можно ли изменить заказ
        """
        return self.status == 'pending'

    def update_status(self, new_status, save=True):
        """
        Обновляет статус заказа с установкой временных меток
        """
        old_status = self.status
        self.status = new_status
        
        # Устанавливаем временные метки
        now = timezone.now()
        if new_status == 'confirmed' and old_status == 'pending':
            self.confirmed_at = now
        elif new_status == 'completed':
            self.completed_at = now
        elif new_status == 'cancelled':
            self.cancelled_at = now
        
        if save:
            self.save(update_fields=['status', 'confirmed_at', 'completed_at', 'cancelled_at'])

    def mark_as_paid(self, payment_method=None):
        """
        Отмечает заказ как оплаченный
        """
        self.is_paid = True
        self.paid_at = timezone.now()
        if payment_method:
            self.payment_method = payment_method
        self.save(update_fields=['is_paid', 'paid_at', 'payment_method'])

    @classmethod
    def get_orders_for_restaurant(cls, restaurant, status=None, date_from=None, date_to=None):
        """
        Получает заказы для ресторана с фильтрами
        """
        queryset = cls.objects.filter(restaurant=restaurant)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')


class OrderItem(TimeStampedModel):
    """
    Позиция заказа (блюдо с количеством и опциями)
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )
    
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        verbose_name="Блюдо"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Количество"
    )
    
    # Цена на момент заказа (может отличаться от текущей цены блюда)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за единицу",
        help_text="Цена блюда на момент заказа"
    )
    
    # Дополнительные опции (сохраняем в JSON)
    selected_options = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Выбранные опции",
        help_text="Опции, выбранные клиентом (JSON)"
    )
    
    # Специальные пожелания к блюду
    special_requests = models.TextField(
        blank=True,
        verbose_name="Особые пожелания",
        help_text="Комментарии клиента к конкретному блюду"
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        ordering = ['id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['dish']),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.dish.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        """
        Переопределяем сохранение для установки цены
        """
        if not self.unit_price:
            self.unit_price = self.dish.price
        super().save(*args, **kwargs)

    def clean(self):
        """
        Валидация позиции заказа
        """
        super().clean()
        
        # Проверяем, что блюдо принадлежит тому же ресторану
        if self.dish and self.order:
            if self.dish.restaurant != self.order.restaurant:
                raise ValidationError('Блюдо должно принадлежать тому же ресторану')
        
        # Проверяем, что блюдо доступно
        if self.dish and not self.dish.is_available:
            raise ValidationError('Блюдо недоступно для заказа')

    def get_options_price(self):
        """
        Возвращает общую стоимость выбранных опций
        """
        total_options_price = Decimal('0.00')
        
        if self.selected_options:
            # Получаем актуальные опции блюда
            dish_options = {opt.id: opt for opt in self.dish.options.all()}
            
            for option_data in self.selected_options:
                option_id = option_data.get('id')
                if option_id in dish_options:
                    total_options_price += dish_options[option_id].price_modifier
        
        return total_options_price

    def get_total_price(self):
        """
        Возвращает общую стоимость позиции (цена + опции) * количество
        """
        item_price = self.unit_price + self.get_options_price()
        return item_price * self.quantity

    def get_formatted_options(self):
        """
        Возвращает отформатированный список выбранных опций
        """
        if not self.selected_options:
            return []
        
        # Получаем актуальные опции блюда
        dish_options = {opt.id: opt for opt in self.dish.options.all()}
        formatted_options = []
        
        for option_data in self.selected_options:
            option_id = option_data.get('id')
            if option_id in dish_options:
                option = dish_options[option_id]
                formatted_options.append({
                    'name': option.name,
                    'price_modifier': option.price_modifier,
                })
        
        return formatted_options

    @classmethod
    def create_from_dish(cls, order, dish, quantity=1, options=None, special_requests=''):
        """
        Создает позицию заказа из блюда
        """
        # Подготавливаем данные опций
        selected_options = []
        if options:
            for option in options:
                if isinstance(option, DishOption):
                    selected_options.append({
                        'id': option.id,
                        'name': option.name,
                        'price_modifier': float(option.price_modifier)
                    })
                elif isinstance(option, dict):
                    selected_options.append(option)
        
        return cls.objects.create(
            order=order,
            dish=dish,
            quantity=quantity,
            unit_price=dish.price,
            selected_options=selected_options,
            special_requests=special_requests
        )
