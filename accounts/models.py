from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей для работы с email
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Создание обычного пользователя
        """
        if not email:
            raise ValueError('Email обязательно должен быть указан')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Создание суперпользователя
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя с email как основным полем для входа
    """
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Email адрес для входа в систему"
    )
    
    # Убираем обязательность username
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Имя пользователя"
    )
    
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя",
        blank=True
    )
    
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия",
        blank=True
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтвержден"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    # Используем email для аутентификации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Устанавливаем кастомный менеджер
    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        """
        Возвращает полное имя пользователя
        """
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def save(self, *args, **kwargs):
        """
        Переопределяем save для автоматической генерации username из email
        """
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class PasswordResetToken(TimeStampedModel):
    """
    Модель для токенов сброса пароля
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name="Пользователь"
    )
    
    token = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Токен"
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name="Использован"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="Истекает"
    )

    class Meta:
        verbose_name = "Токен сброса пароля"
        verbose_name_plural = "Токены сброса пароля"
        ordering = ['-created_at']

    def __str__(self):
        return f"Токен для {self.user.email}"

    def is_expired(self):
        """
        Проверяет, не истек ли токен
        """
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def is_valid(self):
        """
        Проверяет валидность токена
        """
        return not self.is_used and not self.is_expired()
