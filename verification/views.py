from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.core.exceptions import PermissionDenied

from .models import RestaurantVerification
from .forms import RestaurantVerificationForm, RestaurantVerificationStatusForm


class VerificationOwnerMixin:
    """
    Миксин для проверки, что пользователь может работать только со своей заявкой
    """
    def get_verification(self):
        """
        Получает заявку на верификацию текущего пользователя
        """
        if not hasattr(self.request.user, 'restaurant_verification'):
            raise Http404("Заявка на верификацию не найдена")
        return self.request.user.restaurant_verification

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_restaurant_owner:
            raise PermissionDenied("У вас нет прав для выполнения этого действия")
        return super().dispatch(request, *args, **kwargs)


class RestaurantVerificationCreateView(LoginRequiredMixin, CreateView):
    """
    Создание новой заявки на верификацию ресторана
    """
    model = RestaurantVerification
    form_class = RestaurantVerificationForm
    template_name = 'verification/create.html'
    success_url = reverse_lazy('verification:status')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_restaurant_owner:
            raise PermissionDenied("У вас нет прав для регистрации ресторана")

        # Проверяем, есть ли уже заявка
        if hasattr(request.user, 'restaurant_verification'):
            verification = request.user.restaurant_verification
            if verification.status in ['pending', 'approved']:
                return redirect('verification:status')
            elif verification.status == 'requires_changes':
                return redirect('verification:edit')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Заявка на верификацию успешно отправлена! Мы рассмотрим её в ближайшее время.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class RestaurantVerificationUpdateView(VerificationOwnerMixin, UpdateView):
    """
    Редактирование заявки на верификацию
    """
    model = RestaurantVerification
    form_class = RestaurantVerificationForm
    template_name = 'verification/edit.html'
    success_url = reverse_lazy('verification:status')

    def get_object(self):
        return self.get_verification()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verification = self.get_verification()
        context['verification'] = verification

        # Определяем тип редактирования
        is_empty_application = (
            not verification.restaurant_name.strip() and
            not verification.address.strip() and
            not verification.phone.strip()
        )
        context['is_empty_application'] = is_empty_application

        if is_empty_application:
            context['page_title'] = 'Заполнение заявки на верификацию'
            context['page_description'] = 'Заполните информацию о вашем ресторане для получения доступа к системе управления'
        else:
            context['page_title'] = 'Редактирование заявки'
            context['page_description'] = 'Внесите необходимые изменения в вашу заявку на верификацию ресторана'

        return context

    def dispatch(self, request, *args, **kwargs):
        # Дополнительная проверка статуса
        verification = self.get_verification()

        # Разрешаем редактирование для следующих статусов:
        # - pending: можно редактировать в любое время
        # - requires_changes: администратор попросил внести изменения
        # - rejected: заявка отклонена, можно исправить и отправить заново
        allowed_statuses = ['pending', 'requires_changes', 'rejected']

        if verification.status not in allowed_statuses:
            return redirect('verification:status')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        verification = self.get_verification()

        # Проверяем, была ли заявка пустой
        was_empty = (
            not verification.restaurant_name.strip() and
            not verification.address.strip() and
            not verification.phone.strip()
        )

        if was_empty:
            # Для пустых заявок просто сохраняем и отправляем на рассмотрение
            response = super().form_valid(form)
            messages.success(self.request, 'Заявка успешно заполнена и отправлена на рассмотрение!')
        else:
            # Для обычных случаев очищаем комментарий и меняем статус
            form.instance.status = 'pending'
            form.instance.admin_comment = ''  # Очищаем комментарий администратора
            response = super().form_valid(form)
            messages.success(self.request, 'Заявка успешно обновлена и отправлена на повторное рассмотрение!')

        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class RestaurantVerificationStatusView(VerificationOwnerMixin, TemplateView):
    """
    Просмотр статуса заявки на верификацию
    """
    template_name = 'verification/status.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verification = self.get_verification()
        context['verification'] = verification

        # Проверяем, является ли заявка пустой (только что созданной при регистрации)
        is_empty_application = (
            not verification.restaurant_name.strip() and
            not verification.address.strip() and
            not verification.phone.strip()
        )
        context['is_empty_application'] = is_empty_application

        # Определяем следующий шаг в зависимости от статуса
        if verification.status == 'pending':
            if is_empty_application:
                context['next_step'] = 'Заполните информацию о ресторане'
                context['status_color'] = 'blue'
                context['button_text'] = 'Заполнить заявку'
            else:
                context['next_step'] = 'Ожидайте рассмотрения заявки'
                context['status_color'] = 'yellow'
                context['button_text'] = 'Редактировать данные заявки'
        elif verification.status == 'approved':
            context['next_step'] = 'Перейти к созданию профиля ресторана'
            context['status_color'] = 'green'
            context['button_text'] = 'Изменение информации'
        elif verification.status == 'rejected':
            context['next_step'] = 'Исправить ошибки и отправить повторно'
            context['status_color'] = 'red'
            context['button_text'] = 'Редактировать данные заявки'
        elif verification.status == 'requires_changes':
            context['next_step'] = 'Внести изменения в заявку'
            context['status_color'] = 'orange'
            context['button_text'] = 'Редактировать данные заявки'
        else:
            # Fallback для неизвестных статусов
            context['next_step'] = 'Обратитесь к администратору'
            context['status_color'] = 'gray'
            context['button_text'] = 'Обновить'

        return context

    def post(self, request, *args, **kwargs):
        """
        Обработка действий пользователя
        """
        verification = self.get_verification()
        action = request.POST.get('action')

        if action == 'create_restaurant' and verification.status == 'approved':
            # Создаем ресторан
            try:
                restaurant = verification.approve()
                messages.success(request, f'Ресторан "{restaurant.name}" успешно создан!')
                return redirect('dashboard:profile')
            except Exception as e:
                messages.error(request, 'Ошибка при создании ресторана. Попробуйте позже.')
                return redirect('verification:status')

        elif action == 'edit_application' and verification.status in ['rejected', 'requires_changes']:
            return redirect('verification:edit')

        return redirect('verification:status')


class RestaurantVerificationAdminUpdateView(UpdateView):
    """
    View для администратора для изменения статуса заявки
    """
    model = RestaurantVerification
    form_class = RestaurantVerificationStatusForm
    template_name = 'verification/admin_update.html'
    success_url = reverse_lazy('verification:admin_list')

    def form_valid(self, form):
        old_status = self.object.status
        new_status = form.cleaned_data['status']

        response = super().form_valid(form)

        # Если статус изменился на "одобрено", создаем ресторан
        if old_status != 'approved' and new_status == 'approved':
            try:
                restaurant = self.object.approve(form.cleaned_data.get('admin_comment', ''))
                messages.success(self.request, f'Заявка одобрена! Создан ресторан "{restaurant.name}".')
            except Exception as e:
                messages.error(self.request, f'Ошибка при создании ресторана: {e}')

        elif new_status == 'rejected':
            self.object.reject(form.cleaned_data.get('admin_comment', ''))
            messages.success(self.request, 'Заявка отклонена.')

        elif new_status == 'requires_changes':
            self.object.request_changes(form.cleaned_data.get('admin_comment', ''))
            messages.success(self.request, 'Отправлен запрос на внесение изменений.')

        return response


class RestaurantVerificationEditInfoView(VerificationOwnerMixin, UpdateView):
    """
    Редактирование информации ресторана после верификации
    """
    model = RestaurantVerification
    form_class = RestaurantVerificationForm
    template_name = 'verification/edit_info.html'
    success_url = reverse_lazy('verification:status')

    def get_object(self):
        verification = self.get_verification()
        # Проверяем, что статус approved (верифицирован)
        if verification.status != 'approved':
            raise PermissionDenied("Редактирование информации доступно только после верификации")
        return verification

    def form_valid(self, form):
        # Проверяем, были ли изменены данные
        current_data = {
            'restaurant_name': self.object.restaurant_name,
            'address': self.object.address,
            'phone': self.object.phone,
            'email': self.object.email,
            'description': self.object.description,
        }

        new_data = {
            'restaurant_name': form.cleaned_data.get('restaurant_name', ''),
            'address': form.cleaned_data.get('restaurant_address', ''),
            'phone': form.cleaned_data.get('restaurant_phone', ''),
            'email': form.cleaned_data.get('email', ''),
            'description': form.cleaned_data.get('description', ''),
        }

        # Если данные изменились, меняем статус на pending
        if current_data != new_data:
            form.instance.status = 'pending'
            form.instance.admin_comment = 'Информация обновлена пользователем. Требуется повторная верификация.'
            messages.info(self.request, 'Информация обновлена! Данные будут повторно проверены администрацией.')
        else:
            messages.info(self.request, 'Изменения сохранены.')

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)
