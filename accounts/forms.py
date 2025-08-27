from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации пользователя
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите email'
        }),
        label='Email'
    )
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите имя'
        }),
        label='Имя'
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите фамилию'
        }),
        label='Фамилия'
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль'
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтверждение пароля'
    )

    is_restaurant_owner = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded',
            'id': 'restaurant_checkbox'
        }),
        label='Зарегистрировать ресторан',
        help_text='Отметьте, если хотите зарегистрировать ресторан и получить доступ к панели управления'
    )

    # Дополнительные поля для ресторана
    restaurant_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Название вашего ресторана',
            'id': 'restaurant_name'
        }),
        label='Название ресторана'
    )

    restaurant_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Полный адрес ресторана',
            'rows': 2,
            'id': 'restaurant_address'
        }),
        label='Адрес ресторана'
    )

    restaurant_phone = forms.CharField(
        max_length=17,
        required=False,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
        )],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': '+7 (999) 999-99-99',
            'id': 'restaurant_phone'
        }),
        label='Телефон ресторана'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_restaurant_owner', 'restaurant_name', 'restaurant_address', 'restaurant_phone')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email.lower()

    def clean(self):
        cleaned_data = super().clean()
        is_restaurant_owner = cleaned_data.get('is_restaurant_owner')

        if is_restaurant_owner:
            # Если пользователь хочет зарегистрировать ресторан,
            # делаем поля ресторана обязательными
            restaurant_name = cleaned_data.get('restaurant_name')
            restaurant_address = cleaned_data.get('restaurant_address')
            restaurant_phone = cleaned_data.get('restaurant_phone')

            if not restaurant_name or not restaurant_name.strip():
                self.add_error('restaurant_name', 'Название ресторана обязательно для заполнения')

            if not restaurant_address or not restaurant_address.strip():
                self.add_error('restaurant_address', 'Адрес ресторана обязателен для заполнения')

            if not restaurant_phone or not restaurant_phone.strip():
                self.add_error('restaurant_phone', 'Телефон ресторана обязателен для заполнения')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Используем email как username
        user.is_restaurant_owner = self.cleaned_data.get('is_restaurant_owner', False)
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Форма входа в систему
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите email',
            'autofocus': True
        }),
        label='Email'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль'
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username.lower() if username else username


class CustomPasswordResetForm(PasswordResetForm):
    """
    Форма сброса пароля
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите email'
        }),
        label='Email'
    )


class UserProfileForm(forms.ModelForm):
    """
    Форма редактирования профиля пользователя
    """
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите имя'
        }),
        label='Имя'
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Введите фамилию'
        }),
        label='Фамилия'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.strip():
            raise ValidationError('Имя не может быть пустым')
        return first_name.strip()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.strip():
            raise ValidationError('Фамилия не может быть пустой')
        return last_name.strip() 