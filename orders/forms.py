from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Order, OrderItem


class OrderUpdateForm(forms.ModelForm):
    """
    Форма для редактирования заказа
    """
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email', 
            'table_number', 'status', 'payment_method', 'is_paid',
            'special_requests', 'estimated_ready_time'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Имя клиента'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'email@example.com'
            }),
            'table_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Номер стола'
            }),
            'status': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Особые пожелания клиента',
                'rows': 3
            }),
            'estimated_ready_time': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'datetime-local'
            }),
            'is_paid': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            })
        }

    def __init__(self, *args, **kwargs):
        self.restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор статуса в зависимости от текущего статуса
        if self.instance and self.instance.pk:
            current_status = self.instance.status
            
            # Ограничиваем возможные переходы статусов
            if current_status == 'pending':
                allowed_statuses = ['pending', 'confirmed', 'cancelled']
            elif current_status == 'confirmed':
                allowed_statuses = ['confirmed', 'preparing', 'cancelled']
            elif current_status == 'preparing':
                allowed_statuses = ['preparing', 'ready', 'cancelled']
            elif current_status == 'ready':
                allowed_statuses = ['ready', 'completed']
            elif current_status in ['completed', 'cancelled']:
                allowed_statuses = [current_status]  # Нельзя изменить финальные статусы
            else:
                allowed_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
            
            # Фильтруем choices
            filtered_choices = [
                choice for choice in Order.STATUS_CHOICES 
                if choice[0] in allowed_statuses
            ]
            self.fields['status'].choices = filtered_choices
        
        # Ограничиваем выбор способа оплаты
        payment_choices = [('', 'Не указан')] + list(Order.PAYMENT_METHOD_CHOICES)
        self.fields['payment_method'].choices = payment_choices

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone')
        if phone:
            # Простая валидация номера телефона
            import re
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if len(phone_clean) < 10:
                raise ValidationError('Введите корректный номер телефона')
        return phone

    def clean_estimated_ready_time(self):
        estimated_time = self.cleaned_data.get('estimated_ready_time')
        if estimated_time:
            if estimated_time < timezone.now():
                raise ValidationError('Время готовности не может быть в прошлом')
        return estimated_time

    def clean_status(self):
        status = self.cleaned_data.get('status')
        
        # Проверяем, что заказ можно изменить
        if self.instance and self.instance.pk:
            if not self.instance.can_modify() and status != self.instance.status:
                if self.instance.status not in ['pending', 'confirmed', 'preparing', 'ready']:
                    raise ValidationError('Нельзя изменить статус завершенного или отмененного заказа')
        
        return status


class OrderFilterForm(forms.Form):
    """
    Форма для фильтрации заказов
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Поиск по номеру заказа, имени клиента, телефону'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Все статусы')] + Order.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    is_paid = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Все заказы'),
            ('true', 'Только оплаченные'),
            ('false', 'Только неоплаченные')
        ],
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    date_filter = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'За все время'),
            ('today', 'Сегодня'),
            ('yesterday', 'Вчера'),
            ('week', 'За неделю'),
            ('month', 'За месяц')
        ],
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    payment_method = forms.ChoiceField(
        required=False,
        choices=[('', 'Все способы оплаты')] + Order.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )


class OrderStatusForm(forms.Form):
    """
    Форма для быстрого изменения статуса заказа
    """
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )

    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop('current_status', None)
        super().__init__(*args, **kwargs)
        
        if current_status:
            # Ограничиваем выбор статуса в зависимости от текущего
            if current_status == 'pending':
                allowed_statuses = ['confirmed', 'cancelled']
            elif current_status == 'confirmed':
                allowed_statuses = ['preparing', 'cancelled']
            elif current_status == 'preparing':
                allowed_statuses = ['ready', 'cancelled']
            elif current_status == 'ready':
                allowed_statuses = ['completed']
            else:
                allowed_statuses = []
            
            if allowed_statuses:
                filtered_choices = [
                    choice for choice in Order.STATUS_CHOICES 
                    if choice[0] in allowed_statuses
                ]
                self.fields['status'].choices = filtered_choices


class OrderPaymentForm(forms.Form):
    """
    Форма для отметки заказа как оплаченного
    """
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )


class OrderStatsFilterForm(forms.Form):
    """
    Форма для фильтрации статистики заказов
    """
    period = forms.ChoiceField(
        choices=[
            ('today', 'Сегодня'),
            ('week', 'За неделю'),
            ('month', 'За месяц'),
            ('custom', 'Произвольный период')
        ],
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'type': 'date'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if period == 'custom':
            if not start_date or not end_date:
                raise ValidationError('Для произвольного периода укажите начальную и конечную даты')
            
            if start_date > end_date:
                raise ValidationError('Начальная дата не может быть позже конечной')
            
            if end_date > timezone.now().date():
                raise ValidationError('Конечная дата не может быть в будущем')
        
        return cleaned_data


class BulkOrderActionForm(forms.Form):
    """
    Форма для массовых операций с заказами
    """
    ACTION_CHOICES = [
        ('', 'Выберите действие'),
        ('confirm', 'Подтвердить'),
        ('prepare', 'Отправить в готовку'),
        ('ready', 'Отметить готовыми'),
        ('complete', 'Завершить'),
        ('mark_paid', 'Отметить оплаченными'),
        ('mark_unpaid', 'Отметить неоплаченными'),
        ('export', 'Экспортировать')
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    selected_orders = forms.CharField(
        widget=forms.HiddenInput()
    )

    def clean_action(self):
        action = self.cleaned_data.get('action')
        if not action:
            raise ValidationError('Выберите действие')
        return action


class OrderItemForm(forms.ModelForm):
    """
    Форма для редактирования позиции заказа
    """
    
    class Meta:
        model = OrderItem
        fields = ['dish', 'quantity', 'special_requests']
        widgets = {
            'dish': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '1'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Особые пожелания к блюду',
                'rows': 2
            })
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор блюд
        if restaurant:
            from menu.models import Dish
            self.fields['dish'].queryset = Dish.objects.filter(
                restaurant=restaurant, is_available=True
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity < 1:
            raise ValidationError('Количество должно быть больше нуля')
        return quantity


class QuickOrderForm(forms.Form):
    """
    Форма для быстрого создания заказа (только для демо)
    """
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Имя клиента'
        })
    )
    
    table_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Номер стола'
        })
    )
    
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Заметки к заказу',
            'rows': 2
        })
    ) 