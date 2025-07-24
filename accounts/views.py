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
    success_url = reverse_lazy('dashboard:profile')

    def dispatch(self, request, *args, **kwargs):
        # Перенаправляем авторизованных пользователей
        if request.user.is_authenticated:
            return redirect('dashboard:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Автоматически авторизуем пользователя после регистрации
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация успешно завершена! Добро пожаловать!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    """
    Вход в систему
    """
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # Если у пользователя есть ресторан, перенаправляем в дашборд
        if hasattr(self.request.user, 'restaurantprofile'):
            return reverse_lazy('dashboard:profile')
        else:
            # Если нет ресторана, перенаправляем на создание профиля
            return reverse_lazy('dashboard:profile_create')

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
        context['user'] = self.request.user
        context['has_restaurant'] = hasattr(self.request.user, 'restaurantprofile')
        if context['has_restaurant']:
            context['restaurant'] = self.request.user.restaurantprofile
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
