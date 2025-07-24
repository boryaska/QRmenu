from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, PasswordResetToken


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')

    def validate(self, attrs):
        """
        Проверяем совпадение паролей
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs

    def validate_email(self, value):
        """
        Проверяем уникальность email
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def create(self, validated_data):
        """
        Создаем пользователя
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для авторизации пользователя
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )

    def validate_email(self, value):
        """
        Проверяем формат email
        """
        return value.lower()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля пользователя
    """
    full_name = serializers.SerializerMethodField()
    has_restaurant = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_verified', 'has_restaurant', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'email', 'is_verified', 'date_joined', 'last_login')

    def get_full_name(self, obj):
        """
        Возвращаем полное имя пользователя
        """
        return obj.get_full_name()

    def get_has_restaurant(self, obj):
        """
        Проверяем, есть ли у пользователя ресторан
        """
        return hasattr(obj, 'restaurantprofile')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля пользователя
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def validate_first_name(self, value):
        """
        Проверяем имя
        """
        if not value.strip():
            raise serializers.ValidationError("Имя не может быть пустым")
        return value.strip()

    def validate_last_name(self, value):
        """
        Проверяем фамилию
        """
        if not value.strip():
            raise serializers.ValidationError("Фамилия не может быть пустой")
        return value.strip()


class PasswordChangeSerializer(serializers.Serializer):
    """
    Сериализатор для смены пароля
    """
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """
        Проверяем старый пароль
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль")
        return value

    def validate(self, attrs):
        """
        Проверяем совпадение новых паролей
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Новые пароли не совпадают")
        return attrs

    def save(self):
        """
        Сохраняем новый пароль
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """
    Сериализатор для запроса сброса пароля
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Нормализуем email
        """
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля
    """
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """
        Проверяем совпадение паролей
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs


class EmailVerifySerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения email
    """
    token = serializers.CharField()

    def validate_token(self, value):
        """
        Проверяем токен подтверждения email
        """
        # Временная заглушка
        return value


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор пользователя (минимальная информация)
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'full_name')

    def get_full_name(self, obj):
        """
        Возвращаем полное имя пользователя
        """
        return obj.get_full_name() 