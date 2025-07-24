from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from restaurants.models import RestaurantProfile
from core.utils import generate_qr_code

User = get_user_model()


@receiver(post_save, sender=RestaurantProfile)
def generate_qr_code_for_restaurant(sender, instance, created, **kwargs):
    """
    Автоматически генерирует QR-код для ресторана после создания профиля
    """
    if created or not instance.qr_code:
        # Генерируем URL для QR-кода
        menu_url = instance.get_menu_url()
        
        # Создаем QR-код
        qr_code_file = generate_qr_code(menu_url)
        
        # Сохраняем QR-код без рекурсивного вызова сигнала
        instance.qr_code.save(
            f'qr_code_{instance.qr_data}.png',
            qr_code_file,
            save=False
        )
        
        # Сохраняем только поле qr_code
        RestaurantProfile.objects.filter(id=instance.id).update(
            qr_code=instance.qr_code
        )


@receiver(post_save, sender=User)
def create_restaurant_profile_signal(sender, instance, created, **kwargs):
    """
    Автоматически создает профиль ресторана для новых пользователей (опционально)
    Этот сигнал отключен по умолчанию - профили создаются вручную
    """
    # Закомментировано, так как не все пользователи должны быть владельцами ресторанов
    # if created:
    #     RestaurantProfile.objects.create(
    #         user=instance,
    #         name=f"Ресторан {instance.email}",
    #         address="",
    #         phone=""
    #     ) 