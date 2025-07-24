from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, UpdateView, View
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal

from core.mixins import RestaurantOwnerMixin, PaginationMixin, SearchMixin
from .models import Order, OrderItem
from .forms import OrderUpdateForm, OrderFilterForm

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

# === PUBLIC API VIEWS (для клиентов) ===

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAPIView(View):
    """
    API для создания заказа клиентом
    """
    def post(self, request, qr_data):
        try:
            # Получаем ресторан по QR-коду
            from restaurants.models import RestaurantProfile
            restaurant = get_object_or_404(RestaurantProfile, qr_data=qr_data, is_active=True)
            
            # Парсим данные заказа
            data = json.loads(request.body)
            
            # Создаем заказ
            order = Order.objects.create(
                restaurant=restaurant,
                customer_name=data.get('customer_name', ''),
                customer_phone=data.get('customer_phone', ''),
                customer_email=data.get('customer_email', ''),
                table_number=data.get('table_number', ''),
                special_requests=data.get('special_requests', ''),
                qr_data=qr_data,
                customer_ip=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Добавляем позиции заказа
            from menu.models import Dish
            total_amount = Decimal('0.00')
            
            for item_data in data.get('items', []):
                dish = get_object_or_404(Dish, id=item_data['dish_id'], restaurant=restaurant, is_available=True)
                quantity = int(item_data.get('quantity', 1))
                special_requests = item_data.get('special_requests', '')
                
                # Создаем позицию заказа
                order_item = OrderItem.objects.create(
                    order=order,
                    dish=dish,
                    quantity=quantity,
                    unit_price=dish.price,
                    special_requests=special_requests
                )
                
                total_amount += order_item.get_total_price()
            
            # Обновляем сумму заказа
            order.subtotal = total_amount
            order.calculate_totals()
            order.save()
            
            return JsonResponse({
                'success': True,
                'order_number': order.order_number,
                'total_amount': float(order.total_amount),
                'message': 'Заказ успешно создан!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DishDetailAPIView(DetailView):
    """
    API для получения детальной информации о блюде
    """
    def get(self, request, qr_data, dish_id):
        try:
            # Получаем ресторан и блюдо
            from restaurants.models import RestaurantProfile
            from menu.models import Dish
            restaurant = get_object_or_404(RestaurantProfile, qr_data=qr_data, is_active=True)
            dish = get_object_or_404(Dish, id=dish_id, restaurant=restaurant, is_available=True)
            
            # Формируем данные блюда
            dish_data = {
                'id': dish.id,
                'name': dish.name,
                'description': dish.description,
                'ingredients': dish.ingredients,
                'price': float(dish.price),
                'image': dish.image.url if dish.image else None,
                'calories': dish.calories,
                'cooking_time': dish.cooking_time,
                'weight': dish.weight,
                'is_spicy': dish.is_spicy,
                'is_vegetarian': dish.is_vegetarian,
                'is_vegan': dish.is_vegan,
                'options': []
            }
            
            # Добавляем опции блюда
            for option in dish.options.filter(is_available=True):
                dish_data['options'].append({
                    'id': option.id,
                    'name': option.name,
                    'price_modifier': float(option.price_modifier),
                    'is_required': option.is_required
                })
            
            return JsonResponse(dish_data)
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=404)


class OrderListView(RestaurantOwnerMixin, SearchMixin, PaginationMixin, ListView):
    """
    Список заказов
    """
    model = Order
    template_name = 'orders/orders.html'
    context_object_name = 'orders'
    paginate_by = 20
    search_fields = ['order_number', 'customer_name', 'customer_phone', 'table_number']

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            items_count=Count('items'),
            total_items=Sum('items__quantity')
        ).select_related('restaurant')
        
        # Фильтр по статусу
        status = self.request.GET.get('status')
        if status and status in dict(Order.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        
        # Фильтр по оплате
        is_paid = self.request.GET.get('is_paid')
        if is_paid in ['true', 'false']:
            queryset = queryset.filter(is_paid=is_paid == 'true')
        
        # Фильтр по дате
        date_filter = self.request.GET.get('date_filter')
        if date_filter == 'today':
            today = timezone.now().date()
            queryset = queryset.filter(created_at__date=today)
        elif date_filter == 'yesterday':
            yesterday = timezone.now().date() - timedelta(days=1)
            queryset = queryset.filter(created_at__date=yesterday)
        elif date_filter == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        elif date_filter == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=month_ago)
        
        # Фильтр по способу оплаты
        payment_method = self.request.GET.get('payment_method')
        if payment_method and payment_method in dict(Order.PAYMENT_METHOD_CHOICES):
            queryset = queryset.filter(payment_method=payment_method)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Передаем фильтры в контекст
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_is_paid'] = self.request.GET.get('is_paid', '')
        context['selected_date_filter'] = self.request.GET.get('date_filter', '')
        context['selected_payment_method'] = self.request.GET.get('payment_method', '')
        
        # Статистика
        restaurant = self.request.user.restaurantprofile
        today = timezone.now().date()
        
        all_orders = Order.objects.filter(restaurant=restaurant)
        today_orders = all_orders.filter(created_at__date=today)
        
        context['stats'] = {
            'total_orders': all_orders.count(),
            'today_orders': today_orders.count(),
            'pending_orders': all_orders.filter(status='pending').count(),
            'preparing_orders': all_orders.filter(status='preparing').count(),
            'ready_orders': all_orders.filter(status='ready').count(),
            'today_revenue': today_orders.filter(is_paid=True).aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'unpaid_orders': all_orders.filter(is_paid=False).count(),
        }
        
        # Варианты для фильтров
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_method_choices'] = Order.PAYMENT_METHOD_CHOICES
        
        return context


class OrderDetailView(RestaurantOwnerMixin, DetailView):
    """
    Детальный просмотр заказа
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = self.object.items.select_related('dish').all()
        context['can_edit'] = self.object.can_modify()
        context['can_cancel'] = self.object.can_cancel()
        
        # История статусов
        context['status_history'] = []
        if self.object.confirmed_at:
            context['status_history'].append({
                'status': 'Подтвержден',
                'timestamp': self.object.confirmed_at
            })
        if self.object.completed_at:
            context['status_history'].append({
                'status': 'Выполнен',
                'timestamp': self.object.completed_at
            })
        if self.object.cancelled_at:
            context['status_history'].append({
                'status': 'Отменен',
                'timestamp': self.object.cancelled_at
            })
        
        return context


class OrderUpdateView(RestaurantOwnerMixin, UpdateView):
    """
    Редактирование заказа
    """
    model = Order
    form_class = OrderUpdateForm
    template_name = 'orders/order_form.html'
    
    def get_success_url(self):
        return reverse_lazy('orders:order_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Заказ успешно обновлен!')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['restaurant'] = self.request.user.restaurantprofile
        return kwargs


class OrderStatusUpdateView(RestaurantOwnerMixin, DetailView):
    """
    Обновление статуса заказа
    """
    model = Order
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.POST.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            messages.error(request, 'Неверный статус заказа')
            return redirect('orders:order_detail', pk=order.pk)
        
        old_status = order.status
        order.update_status(new_status)
        
        messages.success(
            request, 
            f'Статус заказа #{order.order_number} изменен с "{order.get_status_display()}" на "{dict(Order.STATUS_CHOICES)[new_status]}"'
        )
        
        return redirect('orders:order_detail', pk=order.pk)


class OrderPaymentUpdateView(RestaurantOwnerMixin, DetailView):
    """
    Обновление статуса оплаты заказа
    """
    model = Order
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        payment_method = request.POST.get('payment_method', '')
        
        if not order.is_paid:
            order.mark_as_paid(payment_method)
            messages.success(request, f'Заказ #{order.order_number} отмечен как оплаченный')
        else:
            order.is_paid = False
            order.paid_at = None
            order.payment_method = ''
            order.save(update_fields=['is_paid', 'paid_at', 'payment_method'])
            messages.success(request, f'Заказ #{order.order_number} отмечен как неоплаченный')
        
        return redirect('orders:order_detail', pk=order.pk)


class OrderDashboardView(RestaurantOwnerMixin, ListView):
    """
    Дашборд заказов (активные заказы)
    """
    model = Order
    template_name = 'orders/dashboard.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Показываем только активные заказы
        return super().get_queryset().filter(
            status__in=['pending', 'confirmed', 'preparing', 'ready']
        ).annotate(
            items_count=Count('items')
        ).order_by('created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Группируем заказы по статусам
        orders = self.get_queryset()
        context['pending_orders'] = orders.filter(status='pending')
        context['confirmed_orders'] = orders.filter(status='confirmed')
        context['preparing_orders'] = orders.filter(status='preparing')
        context['ready_orders'] = orders.filter(status='ready')
        
        # Статистика за день
        today = timezone.now().date()
        today_orders = Order.objects.filter(
            restaurant=self.request.user.restaurantprofile,
            created_at__date=today
        )
        
        context['today_stats'] = {
            'total_orders': today_orders.count(),
            'completed_orders': today_orders.filter(status='completed').count(),
            'revenue': today_orders.filter(is_paid=True).aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'average_order': today_orders.aggregate(
                avg=Sum('total_amount')
            )['avg'] or 0,
        }
        
        if context['today_stats']['total_orders'] > 0:
            context['today_stats']['average_order'] = (
                context['today_stats']['revenue'] / context['today_stats']['total_orders']
            )
        
        return context


class OrderStatsView(RestaurantOwnerMixin, ListView):
    """
    Статистика заказов
    """
    model = Order
    template_name = 'orders/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.request.user.restaurantprofile
        
        # Выбираем период
        period = self.request.GET.get('period', 'week')
        
        if period == 'today':
            start_date = timezone.now().date()
            end_date = start_date
        elif period == 'week':
            start_date = timezone.now().date() - timedelta(days=7)
            end_date = timezone.now().date()
        elif period == 'month':
            start_date = timezone.now().date() - timedelta(days=30)
            end_date = timezone.now().date()
        else:
            start_date = timezone.now().date() - timedelta(days=7)
            end_date = timezone.now().date()
        
        orders = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__range=[start_date, end_date]
        )
        
        # Общая статистика
        context['stats'] = {
            'total_orders': orders.count(),
            'completed_orders': orders.filter(status='completed').count(),
            'cancelled_orders': orders.filter(status='cancelled').count(),
            'total_revenue': orders.filter(is_paid=True).aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'average_order_value': 0,
            'total_items': orders.aggregate(
                total=Sum('items__quantity')
            )['total'] or 0,
        }
        
        if context['stats']['total_orders'] > 0:
            context['stats']['average_order_value'] = (
                context['stats']['total_revenue'] / context['stats']['total_orders']
            )
        
        # Статистика по статусам
        context['status_stats'] = []
        for status_code, status_name in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            percentage = (count / context['stats']['total_orders'] * 100) if context['stats']['total_orders'] > 0 else 0
            context['status_stats'].append({
                'status': status_name,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        # Статистика по способам оплаты
        context['payment_stats'] = []
        for method_code, method_name in Order.PAYMENT_METHOD_CHOICES:
            count = orders.filter(payment_method=method_code, is_paid=True).count()
            percentage = (count / context['stats']['total_orders'] * 100) if context['stats']['total_orders'] > 0 else 0
            context['payment_stats'].append({
                'method': method_name,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        context['selected_period'] = period
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        return context


# API view для обновления статуса заказа (AJAX)
class OrderStatusAPIView(RestaurantOwnerMixin, DetailView):
    """
    API для обновления статуса заказа через AJAX
    """
    model = Order
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.POST.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Неверный статус'})
        
        old_status = order.status
        order.update_status(new_status)
        
        return JsonResponse({
            'success': True,
            'message': f'Статус изменен с "{dict(Order.STATUS_CHOICES)[old_status]}" на "{dict(Order.STATUS_CHOICES)[new_status]}"',
            'new_status': new_status,
            'new_status_display': dict(Order.STATUS_CHOICES)[new_status]
        })
