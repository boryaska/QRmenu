from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

from core.utils import validate_image_file
from .models import Category, Dish, DishOption, DishIngredient


class CategoryForm(forms.ModelForm):
    """
    Форма для создания и редактирования категорий
    """
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Название категории'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Описание категории',
                'rows': 3
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise ValidationError('Название категории обязательно')
        
        # Проверяем уникальность в рамках ресторана
        restaurant = getattr(self.instance, 'restaurant', None)
        if restaurant:
            existing = Category.objects.filter(
                restaurant=restaurant, 
                name__iexact=name.strip()
            )
            
            # Для существующего объекта исключаем его самого
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Категория с таким названием уже существует')
        
        return name.strip()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            validate_image_file(image)
        return image

    def clean_sort_order(self):
        sort_order = self.cleaned_data.get('sort_order')
        if sort_order is not None and sort_order < 0:
            raise ValidationError('Порядок сортировки не может быть отрицательным')
        return sort_order


class DishForm(forms.ModelForm):
    """
    Форма для создания и редактирования блюд
    """
    
    class Meta:
        model = Dish
        fields = [
            'category', 'name', 'description', 'ingredients', 'price',
            'image', 'calories', 'proteins', 'fats', 'carbohydrates',
            'weight', 'weight_unit', 'cooking_time', 'is_popular', 'is_new', 'is_spicy',
            'is_vegetarian', 'is_vegan', 'is_available', 'sort_order'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Название блюда'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Описание блюда',
                'rows': 4
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Состав блюда (через запятую)',
                'rows': 3
            }),
            'price': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            }),
            'calories': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0',
                'placeholder': 'ккал на 100г'
            }),
            'proteins': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'г на 100г'
            }),
            'fats': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'г на 100г'
            }),
            'carbohydrates': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'г на 100г'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0',
                'placeholder': 'количество'
            }),
            'weight_unit': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'cooking_time': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0',
                'placeholder': 'минут'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Состав блюда (через запятую)',
                'rows': 3
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0'
            }),
            # Чекбоксы
            'is_popular': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_new': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_spicy': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_vegetarian': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_vegan': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            })
        }

    def __init__(self, *args, **kwargs):
        self.restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор категорий
        if self.restaurant:
            self.fields['category'].queryset = Category.objects.filter(
                restaurant=self.restaurant, is_active=True
            )
        else:
            # Если ресторан не передан, показываем пустой queryset
            self.fields['category'].queryset = Category.objects.none()
            # Добавляем помощь пользователю
            self.fields['category'].help_text = "Сначала создайте категории в разделе 'Категории'"

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise ValidationError('Название блюда обязательно')
        
        # Проверяем уникальность в рамках ресторана
        if self.restaurant:
            existing = Dish.objects.filter(
                restaurant=self.restaurant, 
                name__iexact=name.strip()
            )
            
            # Для существующего объекта исключаем его самого
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Блюдо с таким названием уже существует')
        
        return name.strip()

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise ValidationError('Цена должна быть больше нуля')
        return price

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            validate_image_file(image)
        return image

    def clean_category(self):
        category = self.cleaned_data.get('category')
        
        # Проверяем, что категория выбрана
        if not category:
            raise ValidationError('Выберите категорию для блюда')
            
        # Проверяем принадлежность категории ресторану
        if category and self.restaurant:
            if category.restaurant != self.restaurant:
                raise ValidationError('Выберите категорию из вашего ресторана')
        elif category and not self.restaurant:
            raise ValidationError('Ошибка: ресторан не определен')
            
        return category

    def clean(self):
        cleaned_data = super().clean()
        
        # Проверяем, что ресторан определен
        if not self.restaurant:
            raise ValidationError('Ошибка: не удалось определить ресторан. Обратитесь к администратору.')
        
        # Если блюдо веганское, то оно автоматически вегетарианское
        if cleaned_data.get('is_vegan'):
            cleaned_data['is_vegetarian'] = True
        
        return cleaned_data


class DishOptionForm(forms.ModelForm):
    """
    Форма для создания и редактирования опций блюда
    """
    
    class Meta:
        model = DishOption
        fields = ['name', 'price_modifier', 'is_required', 'is_available', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Название опции'
            }),
            'price_modifier': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise ValidationError('Название опции обязательно')
        return name.strip()


class DishIngredientForm(forms.ModelForm):
    """
    Форма для ингредиентов блюда
    """
    
    class Meta:
        model = DishIngredient
        fields = ['name', 'quantity', 'is_allergen', 'can_exclude']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Название ингредиента'
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': '200г, 2 шт, по вкусу'
            }),
            'is_allergen': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
            }),
            'can_exclude': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise ValidationError('Название ингредиента обязательно')
        return name.strip()


# Вспомогательная форма для массовых операций
class BulkActionForm(forms.Form):
    """
    Форма для массовых операций с блюдами
    """
    ACTION_CHOICES = [
        ('', 'Выберите действие'),
        ('make_available', 'Сделать доступными'),
        ('make_unavailable', 'Сделать недоступными'),
        ('mark_popular', 'Отметить как популярные'),
        ('unmark_popular', 'Убрать отметку популярности'),
        ('mark_new', 'Отметить как новинки'),
        ('unmark_new', 'Убрать отметку новинки'),
        ('delete', 'Удалить')
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    selected_items = forms.CharField(
        widget=forms.HiddenInput()
    )

    def clean_action(self):
        action = self.cleaned_data.get('action')
        if not action:
            raise ValidationError('Выберите действие')
        return action


class CategoryFilterForm(forms.Form):
    """
    Форма для фильтрации категорий
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Поиск по названию или описанию'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Все категории'),
            ('true', 'Только активные'),
            ('false', 'Только неактивные')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )


class DishFilterForm(forms.Form):
    """
    Форма для фильтрации блюд
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Поиск по названию, описанию или составу'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label='Все категории',
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    is_available = forms.ChoiceField(
        choices=[
            ('', 'Все блюда'),
            ('true', 'Только доступные'),
            ('false', 'Только недоступные')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    is_popular = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
        })
    )
    
    is_new = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
        })
    )
    
    is_vegetarian = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500'
        })
    )

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        
        if restaurant:
            self.fields['category'].queryset = Category.objects.filter(
                restaurant=restaurant, is_active=True
            ) 