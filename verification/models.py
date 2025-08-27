from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from core.utils import UniqueFilenameStorage


class RestaurantVerification(TimeStampedModel):
    """
    Модель заявки на верификацию ресторана
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает рассмотрения'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('requires_changes', 'Требует изменений'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='restaurant_verification',
        verbose_name="Пользователь"
    )

    # Основная информация о ресторане
    restaurant_name = models.CharField(
        max_length=200,
        verbose_name="Название ресторана",
        help_text="Полное название вашего ресторана"
    )

    address = models.TextField(
        verbose_name="Адрес",
        help_text="Полный адрес ресторана с указанием города, улицы, номера здания"
    )

    phone = models.CharField(
        max_length=17,
        verbose_name="Контактный телефон",
        help_text="Номер телефона для связи с администрацией"
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Контактный email",
        help_text="Email для связи (если отличается от основного)"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание ресторана",
        help_text="Краткое описание концепции, кухни, особенностей"
    )

    # Документы для верификации
    document_file = models.FileField(
        upload_to='verification/documents/',
        blank=True,
        null=True,
        max_length=255,
        storage=UniqueFilenameStorage(),
        verbose_name="Документ",
        help_text="Загрузите документ, подтверждающий право на ведение деятельности (ИНН, свидетельство и т.д.)"
    )

    # Статус заявки
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус заявки"
    )

    # Комментарии администратора
    admin_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий администратора",
        help_text="Комментарий администратора при рассмотрении заявки"
    )

    # Даты
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата подачи заявки"
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата рассмотрения"
    )

    class Meta:
        verbose_name = "Заявка на верификацию ресторана"
        verbose_name_plural = "Заявки на верификацию ресторанов"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Заявка от {self.user.email} на ресторан '{self.restaurant_name}'"

    def get_status_display_color(self):
        """
        Возвращает цвет для отображения статуса
        """
        colors = {
            'pending': 'yellow',
            'approved': 'green',
            'rejected': 'red',
            'requires_changes': 'orange',
        }
        return colors.get(self.status, 'gray')

    def is_pending(self):
        """Проверяет, находится ли заявка на рассмотрении"""
        return self.status == 'pending'

    def is_approved(self):
        """Проверяет, одобрена ли заявка"""
        return self.status == 'approved'

    def is_rejected(self):
        """Проверяет, отклонена ли заявка"""
        return self.status == 'rejected'

    def approve(self, admin_comment=''):
        """
        Одобряет заявку и создает ресторан
        """
        from django.utils import timezone
        from restaurants.models import RestaurantProfile, RestaurantSettings

        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.admin_comment = admin_comment
        self.save()

        # Создаем профиль ресторана
        restaurant = RestaurantProfile.objects.create(
            user=self.user,
            name=self.restaurant_name,
            description=self.description,
            address=self.address,
            phone=self.phone,
            email=self.email or self.user.email,
        )

        # Создаем настройки ресторана
        RestaurantSettings.objects.create(restaurant=restaurant)

        # Обновляем статус пользователя
        self.user.is_restaurant_owner = True
        self.user.save()

        return restaurant

    def reject(self, admin_comment=''):
        """
        Отклоняет заявку
        """
        from django.utils import timezone

        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.admin_comment = admin_comment
        self.save()

    def request_changes(self, admin_comment=''):
        """
        Запрашивает изменения в заявке
        """
        self.status = 'requires_changes'
        self.admin_comment = admin_comment
        self.save()
