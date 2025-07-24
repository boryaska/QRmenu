from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from core.models import TimeStampedModel
from core.utils import validate_image_file, slugify_filename
from restaurants.models import RestaurantProfile


def dish_image_upload_path(instance, filename):
    """
    Определяет путь для загрузки изображений блюд
    """
    safe_filename = slugify_filename(filename)
    
    # Пытаемся получить ресторан
    restaurant = None
    if hasattr(instance, 'restaurant') and instance.restaurant:
        restaurant = instance.restaurant
    elif hasattr(instance, 'category') and instance.category and instance.category.restaurant:
        restaurant = instance.category.restaurant
    
    if restaurant:
        return f'restaurants/{restaurant.qr_data}/dishes/{safe_filename}'
    else:
        # Если ресторан не найден, используем временный путь
        return f'temp/dishes/{safe_filename}'


def category_image_upload_path(instance, filename):
    """
    Определяет путь для загрузки изображений категорий
    """
    safe_filename = slugify_filename(filename)
    
    # Пытаемся получить ресторан
    if hasattr(instance, 'restaurant') and instance.restaurant:
        return f'restaurants/{instance.restaurant.qr_data}/categories/{safe_filename}'
    else:
        # Если ресторан не найден, используем временный путь
        return f'temp/categories/{safe_filename}'


class Category(TimeStampedModel):
    """
    Категория меню (например: Салаты, Основные блюда, Десерты)
    """
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="Ресторан"
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название категории",
        help_text="Например: Салаты, Основные блюда"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Краткое описание категории"
    )
    
    image = models.ImageField(
        upload_to=category_image_upload_path,
        blank=True,
        null=True,
        verbose_name="Изображение",
        help_text="Изображение категории (необязательно)"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки",
        help_text="Порядок отображения категории в меню"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
        help_text="Отображается ли категория в меню"
    )
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['sort_order', 'name']
        unique_together = ['restaurant', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'is_active']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        if self.restaurant:
            return f"{self.restaurant.name} - {self.name}"
        return self.name

    def clean(self):
        """
        Валидация модели
        """
        super().clean()
        
        # Проверяем изображение при загрузке
        if self.image:
            validate_image_file(self.image)

    def get_active_dishes_count(self):
        """
        Возвращает количество активных блюд в категории
        """
        return self.dishes.filter(is_available=True).count()

    def get_min_price(self):
        """
        Возвращает минимальную цену блюда в категории
        """
        min_price = self.dishes.filter(is_available=True).aggregate(
            min_price=models.Min('price')
        )['min_price']
        return min_price or Decimal('0.00')


class Dish(TimeStampedModel):
    """
    Блюдо в меню
    """
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='dishes',
        verbose_name="Ресторан"
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='dishes',
        verbose_name="Категория"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Название блюда",
        help_text="Название блюда в меню"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Подробное описание блюда"
    )
    
    ingredients = models.TextField(
        blank=True,
        verbose_name="Состав",
        help_text="Список ингредиентов через запятую"
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Цена",
        help_text="Цена блюда"
    )
    
    image = models.ImageField(
        upload_to=dish_image_upload_path,
        blank=True,
        null=True,
        verbose_name="Изображение",
        help_text="Фото блюда"
    )
    
    # Пищевая ценность
    calories = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Калории",
        help_text="Калорийность на 100г"
    )
    
    proteins = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Белки (г)",
        help_text="Количество белков на 100г"
    )
    
    fats = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Жиры (г)",
        help_text="Количество жиров на 100г"
    )
    
    carbohydrates = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Углеводы (г)",
        help_text="Количество углеводов на 100г"
    )
    
    # Дополнительная информация
    weight = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Вес (г)",
        help_text="Вес порции в граммах"
    )
    
    cooking_time = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Время приготовления (мин)",
        help_text="Время приготовления в минутах"
    )
    
    # Настройки и статус
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки"
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name="Доступно",
        help_text="Доступно ли блюдо для заказа"
    )
    
    is_popular = models.BooleanField(
        default=False,
        verbose_name="Популярное",
        help_text="Отмечать как популярное блюдо"
    )
    
    is_new = models.BooleanField(
        default=False,
        verbose_name="Новинка",
        help_text="Отмечать как новое блюдо"
    )
    
    is_spicy = models.BooleanField(
        default=False,
        verbose_name="Острое",
        help_text="Острое блюдо"
    )
    
    is_vegetarian = models.BooleanField(
        default=False,
        verbose_name="Вегетарианское",
        help_text="Подходит для вегетарианцев"
    )
    
    is_vegan = models.BooleanField(
        default=False,
        verbose_name="Веганское",
        help_text="Подходит для веганов"
    )

    class Meta:
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"
        ordering = ['category__sort_order', 'sort_order', 'name']
        unique_together = ['restaurant', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'is_available']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['is_popular']),
            models.Index(fields=['is_new']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        if self.restaurant:
            return f"{self.restaurant.name} - {self.name}"
        return self.name

    def clean(self):
        """
        Валидация модели
        """
        super().clean()
        
        # Проверяем, что категория принадлежит тому же ресторану
        # Получаем ресторан безопасно
        restaurant = None
        if hasattr(self, 'restaurant') and self.restaurant_id:
            restaurant = self.restaurant
        elif self.category and self.category.restaurant:
            restaurant = self.category.restaurant
            
        if self.category and restaurant:
            if self.category.restaurant != restaurant:
                raise ValidationError('Категория должна принадлежать тому же ресторану')
        
        # Проверяем изображение
        if self.image:
            validate_image_file(self.image)
        
        # Проверяем цену
        if hasattr(self, 'price') and self.price and self.price <= 0:
            raise ValidationError('Цена должна быть больше нуля')

    def save(self, *args, **kwargs):
        """
        Переопределяем сохранение для автоматической установки ресторана
        """
        if self.category and not self.restaurant_id:
            self.restaurant = self.category.restaurant
        super().save(*args, **kwargs)

    def get_formatted_price(self):
        """
        Возвращает отформатированную цену с валютой ресторана
        """
        # Получаем ресторан безопасно
        restaurant = None
        if hasattr(self, 'restaurant') and self.restaurant_id:
            restaurant = self.restaurant
        elif hasattr(self, 'category') and self.category and self.category.restaurant:
            restaurant = self.category.restaurant
            
        if restaurant:
            return restaurant.format_price(self.price)
        else:
            # Если ресторан не найден, возвращаем простое форматирование
            return f"{self.price} ₽"

    def get_badges(self):
        """
        Возвращает список меток для блюда
        """
        badges = []
        if self.is_new:
            badges.append({'text': 'Новинка', 'class': 'badge-new'})
        if self.is_popular:
            badges.append({'text': 'Популярное', 'class': 'badge-popular'})
        if self.is_spicy:
            badges.append({'text': 'Острое', 'class': 'badge-spicy'})
        if self.is_vegetarian:
            badges.append({'text': 'Вегетарианское', 'class': 'badge-vegetarian'})
        if self.is_vegan:
            badges.append({'text': 'Веганское', 'class': 'badge-vegan'})
        return badges


class DishOption(TimeStampedModel):
    """
    Дополнительные опции для блюда (размер порции, добавки и т.д.)
    """
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name="Блюдо"
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название опции",
        help_text="Например: Большая порция, Сыр, Соус"
    )
    
    price_modifier = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Изменение цены",
        help_text="Дополнительная стоимость (может быть отрицательной)"
    )
    
    is_required = models.BooleanField(
        default=False,
        verbose_name="Обязательная",
        help_text="Обязательна ли эта опция при заказе"
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name="Доступна",
        help_text="Доступна ли опция для выбора"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки"
    )

    class Meta:
        verbose_name = "Опция блюда"
        verbose_name_plural = "Опции блюд"
        ordering = ['sort_order', 'name']
        unique_together = ['dish', 'name']

    def __str__(self):
        price_sign = '+' if self.price_modifier >= 0 else ''
        return f"{self.dish.name} - {self.name} ({price_sign}{self.price_modifier})"

    def get_total_price_with_dish(self):
        """
        Возвращает общую цену блюда с этой опцией
        """
        return self.dish.price + self.price_modifier


class DishIngredient(TimeStampedModel):
    """
    Ингредиенты блюда для детального описания состава
    """
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='dish_ingredients',
        verbose_name="Блюдо"
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название ингредиента"
    )
    
    quantity = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Количество",
        help_text="Например: 200г, 2 шт, по вкусу"
    )
    
    is_allergen = models.BooleanField(
        default=False,
        verbose_name="Аллерген",
        help_text="Является ли ингредиент аллергеном"
    )
    
    can_exclude = models.BooleanField(
        default=True,
        verbose_name="Можно исключить",
        help_text="Можно ли исключить ингредиент из блюда"
    )

    class Meta:
        verbose_name = "Ингредиент блюда"
        verbose_name_plural = "Ингредиенты блюд"
        ordering = ['name']
        unique_together = ['dish', 'name']

    def __str__(self):
        quantity_str = f" ({self.quantity})" if self.quantity else ""
        return f"{self.dish.name} - {self.name}{quantity_str}"
