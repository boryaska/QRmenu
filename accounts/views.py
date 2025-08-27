from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from .models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, UserProfileForm


class SignUpView(CreateView):
    """
    Регистрация нового пользователя
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'

    def dispatch(self, request, *args, **kwargs):
        # Перенаправляем авторизованных пользователей
        if request.user.is_authenticated:
            # Определяем куда перенаправить пользователя в зависимости от его типа
            if request.user.is_restaurant_owner:
                # Ресторатор - проверяем статус верификации
                if hasattr(request.user, 'restaurant_verification'):
                    verification = request.user.restaurant_verification
                    if verification.status == 'approved' and hasattr(request.user, 'restaurantprofile'):
                        return redirect('dashboard:profile')
                    else:
                        return redirect('verification:status')
                else:
                    return redirect('verification:create')
            else:
                # Обычный пользователь - в каталог ресторанов
                return redirect('clients:catalog')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        # Если пользователь отметил галочку "ресторан", создаем заявку на верификацию
        if form.cleaned_data.get('is_restaurant_owner'):
            from verification.models import RestaurantVerification
            # Создаем заявку на верификацию с данными из регистрации
            RestaurantVerification.objects.create(
                user=self.object,
                restaurant_name=form.cleaned_data.get('restaurant_name', ''),
                address=form.cleaned_data.get('restaurant_address', ''),
                phone=form.cleaned_data.get('restaurant_phone', ''),
                status='pending'
            )
            messages.info(self.request, 'Регистрация завершена! Ваша заявка на верификацию отправлена и будет рассмотрена в ближайшее время.')

        # Автоматически авторизуем пользователя после регистрации
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация успешно завершена! Добро пожаловать!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)

    def get_success_url(self):
        """
        Определяет URL для перенаправления после успешной регистрации
        """
        user = self.object

        if user.is_restaurant_owner:
            # Ресторатор - перенаправляем на статус верификации
            return reverse_lazy('verification:status')
        else:
            # Обычный пользователь - в каталог ресторанов
            return reverse_lazy('clients:catalog')


class CustomLoginView(LoginView):
    """
    Вход в систему
    """
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user

        # Если пользователь является владельцем ресторана
        if user.is_restaurant_owner:
            # Проверяем статус верификации
            if hasattr(user, 'restaurant_verification'):
                verification = user.restaurant_verification
                if verification.status == 'pending':
                    # Заявка на рассмотрении - перенаправляем на статус верификации
                    return reverse_lazy('verification:status')
                elif verification.status == 'requires_changes':
                    # Нужно внести изменения - перенаправляем на редактирование заявки
                    return reverse_lazy('verification:edit')
                elif verification.status == 'approved':
                    # Верификация одобрена - проверяем есть ли профиль ресторана
                    if hasattr(user, 'restaurantprofile'):
                        return reverse_lazy('dashboard:profile')
                    else:
                        return reverse_lazy('dashboard:profile_create')
                else:  # rejected
                    # Заявка отклонена - перенаправляем на повторную подачу
                    return reverse_lazy('verification:create')
            else:
                # Нет заявки на верификацию - перенаправляем на создание
                return reverse_lazy('verification:create')
        else:
            # Обычный пользователь - перенаправляем на каталог ресторанов
            return reverse_lazy('clients:catalog')

    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().get_full_name()}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Неверный email или пароль.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """
    Выход из системы
    """
    next_page = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            messages.info(request, 'Вы успешно вышли из системы.')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    """
    Сброс пароля
    """
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        messages.success(
            self.request, 
            'Если указанный email существует в нашей системе, на него будет отправлена ссылка для сброса пароля.'
        )
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля пользователя
    """
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Просмотр профиля пользователя
    """
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Оптимизируем запросы для связанных объектов
        user_with_verification = user.__class__.objects.select_related(
            'restaurantprofile',
            'restaurant_verification'
        ).get(pk=user.pk)

        context['user'] = user_with_verification
        context['has_restaurant'] = hasattr(user_with_verification, 'restaurantprofile')
        if context['has_restaurant']:
            context['restaurant'] = user_with_verification.restaurantprofile
        return context


# Вспомогательная view для главной страницы
class HomeView(TemplateView):
    """
    Главная страница сайта
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_authenticated'] = self.request.user.is_authenticated
        return context
