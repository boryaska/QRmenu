from django import forms
from django.core.validators import RegexValidator
from .models import RestaurantVerification


class RestaurantVerificationForm(forms.ModelForm):
    """
    Форма для создания/редактирования заявки на верификацию ресторана
    """
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )

    restaurant_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Название вашего ресторана'
        }),
        label='Название ресторана',
        help_text='Полное название вашего ресторана'
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Полный адрес ресторана',
            'rows': 3
        }),
        label='Адрес ресторана',
        help_text='Полный адрес с указанием города, улицы, номера здания'
    )

    phone = forms.CharField(
        validators=[phone_regex],
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': '+7 (999) 999-99-99'
        }),
        label='Контактный телефон',
        help_text='Номер телефона для связи с администрацией'
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'email@restaurant.com'
        }),
        label='Контактный email',
        help_text='Email для связи (если отличается от основного)'
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Опишите концепцию, кухню, особенности вашего ресторана',
            'rows': 4
        }),
        label='Описание ресторана',
        help_text='Краткое описание концепции, кухни, особенностей'
    )

    document_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
        }),
        label='Документ',
        help_text='Загрузите документ, подтверждающий право на ведение деятельности (ИНН, свидетельство и т.д.). Форматы: PDF, JPG, PNG. Максимум 10MB.'
    )

    class Meta:
        model = RestaurantVerification
        fields = ('restaurant_name', 'address', 'phone', 'email', 'description', 'document_file')

    def clean_document_file(self):
        """
        Валидация загружаемого файла
        """
        file = self.cleaned_data.get('document_file')
        if file:
            # Проверка размера файла (10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 10MB')

            # Проверка типа файла
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Допустимые форматы файлов: PDF, JPG, PNG')

        return file

    def clean_restaurant_name(self):
        """
        Валидация названия ресторана
        """
        name = self.cleaned_data.get('restaurant_name')
        if not name.strip():
            raise forms.ValidationError('Название ресторана обязательно для заполнения')
        return name.strip()

    def clean_address(self):
        """
        Валидация адреса
        """
        address = self.cleaned_data.get('address')
        if not address.strip():
            raise forms.ValidationError('Адрес ресторана обязателен для заполнения')
        return address.strip()

    def clean_phone(self):
        """
        Валидация телефона
        """
        phone = self.cleaned_data.get('phone')
        if not phone.strip():
            raise forms.ValidationError('Телефон обязателен для заполнения')
        return phone.strip()


class RestaurantVerificationStatusForm(forms.ModelForm):
    """
    Форма для администратора для изменения статуса заявки
    """
    admin_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Комментарий для заявителя',
            'rows': 3
        }),
        label='Комментарий администратора',
        help_text='Комментарий будет отправлен заявителю'
    )

    class Meta:
        model = RestaurantVerification
        fields = ('status', 'admin_comment')
