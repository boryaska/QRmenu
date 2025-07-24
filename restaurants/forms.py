from django import forms
from django.core.exceptions import ValidationError
from .models import RestaurantProfile, RestaurantSettings


class RestaurantProfileForm(forms.ModelForm):
    """
    Форма создания и редактирования профиля ресторана
    """
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите название ресторана'
        }),
        label='Название ресторана'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Краткое описание ресторана',
            'rows': 3
        }),
        label='Описание'
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Полный адрес ресторана',
            'rows': 2
        }),
        label='Адрес'
    )
    
    phone = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': '+7 (999) 123-45-67'
        }),
        label='Телефон'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'contact@restaurant.com'
        }),
        label='Email для связи'
    )
    
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'https://yourrestaurant.com'
        }),
        label='Веб-сайт'
    )
    
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
            'accept': 'image/*'
        }),
        label='Логотип'
    )
    
    currency = forms.ChoiceField(
        choices=RestaurantProfile.CURRENCY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        }),
        label='Валюта'
    )
    
    tax_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'step': '0.01',
            'min': '0',
            'max': '100'
        }),
        label='Налог (%)'
    )
    
    service_charge = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'step': '0.01',
            'min': '0',
            'max': '100'
        }),
        label='Сервисный сбор (%)'
    )
    
    table_prefix = forms.CharField(
        max_length=10,
        initial="Стол",
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Стол'
        }),
        label='Префикс столов'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }),
        label='Ресторан активен'
    )

    class Meta:
        model = RestaurantProfile
        fields = [
            'name', 'description', 'address', 'phone', 'email', 'website', 
            'logo', 'currency', 'tax_rate', 'service_charge', 'table_prefix', 'is_active'
        ]

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise ValidationError('Название ресторана не может быть пустым')
        if len(name.strip()) < 2:
            raise ValidationError('Название ресторана должно содержать минимум 2 символа')
        return name.strip()

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address or not address.strip():
            raise ValidationError('Адрес не может быть пустым')
        return address.strip()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone or not phone.strip():
            raise ValidationError('Телефон не может быть пустым')
        return phone.strip()

    def clean_tax_rate(self):
        tax_rate = self.cleaned_data.get('tax_rate')
        if tax_rate < 0 or tax_rate > 100:
            raise ValidationError('Налоговая ставка должна быть от 0 до 100%')
        return tax_rate

    def clean_service_charge(self):
        service_charge = self.cleaned_data.get('service_charge')
        if service_charge < 0 or service_charge > 100:
            raise ValidationError('Сервисный сбор должен быть от 0 до 100%')
        return service_charge


class RestaurantSettingsForm(forms.ModelForm):
    """
    Форма настроек ресторана
    """
    min_order_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'step': '0.01',
            'min': '0'
        }),
        label='Минимальная сумма заказа'
    )
    
    max_order_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=999999.99,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'step': '0.01',
            'min': '0'
        }),
        label='Максимальная сумма заказа'
    )
    
    order_timeout_minutes = forms.IntegerField(
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'min': '1',
            'max': '1440'
        }),
        label='Таймаут заказа (мин)'
    )
    
    email_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }),
        label='Email уведомления'
    )
    
    sms_notifications = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }),
        label='SMS уведомления'
    )
    
    payment_gateway = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Stripe, PayPal, Сбербанк...'
        }),
        label='Платежный шлюз'
    )

    class Meta:
        model = RestaurantSettings
        fields = [
            'min_order_amount', 'max_order_amount', 'order_timeout_minutes',
            'email_notifications', 'sms_notifications', 'payment_gateway'
        ]

    def clean_min_order_amount(self):
        min_amount = self.cleaned_data.get('min_order_amount')
        if min_amount < 0:
            raise ValidationError('Минимальная сумма заказа не может быть отрицательной')
        return min_amount

    def clean_max_order_amount(self):
        max_amount = self.cleaned_data.get('max_order_amount')
        if max_amount <= 0:
            raise ValidationError('Максимальная сумма заказа должна быть больше 0')
        return max_amount

    def clean_order_timeout_minutes(self):
        timeout = self.cleaned_data.get('order_timeout_minutes')
        if timeout < 1 or timeout > 1440:
            raise ValidationError('Таймаут заказа должен быть от 1 до 1440 минут')
        return timeout

    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_order_amount')
        max_amount = cleaned_data.get('max_order_amount')
        
        if min_amount and max_amount and min_amount >= max_amount:
            raise ValidationError('Минимальная сумма заказа должна быть меньше максимальной')
        
        return cleaned_data 