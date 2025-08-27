import io
import uuid
import secrets
import qrcode
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
import os


def generate_restaurant_qr_data():
    """
    Генерирует уникальный идентификатор для QR-кода ресторана
    """
    return f"rest_{uuid.uuid4().hex[:12]}"


def generate_qr_code(data, size=(300, 300)):
    """
    Генерирует QR-код для переданных данных
    
    Args:
        data (str): Данные для кодирования в QR-код
        size (tuple): Размер QR-кода в пикселях
        
    Returns:
        InMemoryUploadedFile: Файл с QR-кодом
    """
    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(data)
    qr.make(fit=True)

    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize(size, Image.Resampling.LANCZOS)

    # Сохраняем в memory buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return InMemoryUploadedFile(
        buffer, None, 'qr_code.png', 'image/png', 
        len(buffer.getvalue()), None
    )


def validate_image_file(file):
    """
    Валидация изображений
    
    Args:
        file: Загружаемый файл
        
    Raises:
        ValidationError: При неверном формате или размере
    """
    if not file:
        return
    
    # Проверяем расширение
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    _, ext = os.path.splitext(file.name.lower())
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Недопустимый формат файла. Разрешены: {", ".join(allowed_extensions)}'
        )
    
    # Проверяем размер (5MB)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError('Файл слишком большой. Максимальный размер: 5MB')
    
    # Проверяем, что это действительно изображение
    try:
        from PIL import Image
        img = Image.open(file)
        img.verify()
        file.seek(0)  # Возвращаем указатель в начало файла
    except Exception:
        raise ValidationError('Файл не является изображением')


def resize_image(file, max_width=800, max_height=600, quality=85):
    """
    Изменяет размер изображения для оптимизации
    
    Args:
        file: Исходный файл изображения
        max_width: Максимальная ширина
        max_height: Максимальная высота  
        quality: Качество JPEG (1-100)
        
    Returns:
        InMemoryUploadedFile: Оптимизированное изображение
    """
    img = Image.open(file)
    
    # Конвертируем в RGB если нужно
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Изменяем размер с сохранением пропорций
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Сохраняем в буфер
    buffer = io.BytesIO()
    format_name = 'JPEG' if file.name.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
    
    if format_name == 'JPEG':
        img.save(buffer, format=format_name, quality=quality, optimize=True)
    else:
        img.save(buffer, format=format_name, optimize=True)
    
    buffer.seek(0)
    
    return InMemoryUploadedFile(
        buffer, None, file.name, f'image/{format_name.lower()}',
        len(buffer.getvalue()), None
    )


def generate_order_number():
    """
    Генерирует уникальный номер заказа
    """
    timestamp = timezone.now().strftime('%Y%m%d%H%M')
    random_part = secrets.token_hex(3).upper()
    return f"ORD-{timestamp}-{random_part}"


def format_currency(amount, currency='RUB'):
    """
    Форматирует сумму с валютой
    
    Args:
        amount (Decimal): Сумма
        currency (str): Код валюты
        
    Returns:
        str: Отформатированная строка
    """
    currency_symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
        'KZT': '₸',
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{amount:.2f} {symbol}"


def slugify_filename(filename):
    """
    Создает безопасное имя файла
    """
    import re
    from django.utils.text import slugify

    name, ext = os.path.splitext(filename)
    name = slugify(name)[:50]  # Ограничиваем длину
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}{ext}"


def generate_unique_filename(filename, prefix='file'):
    """
    Генерирует уникальное короткое имя файла

    Args:
        filename (str): Исходное имя файла
        prefix (str): Префикс для имени файла

    Returns:
        str: Уникальное имя файла
    """
    # Получаем расширение файла
    _, ext = os.path.splitext(filename)

    # Генерируем короткий уникальный идентификатор
    unique_id = secrets.token_hex(8)  # 16 символов

    # Создаем новое имя файла
    timestamp = timezone.now().strftime('%Y%m%d')
    new_filename = f"{prefix}_{timestamp}_{unique_id}{ext}"

    return new_filename


def get_client_ip(request):
    """
    Получает IP-адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calculate_order_total(subtotal, tax_rate=0, service_charge=0):
    """
    Рассчитывает общую сумму заказа с налогами и сборами
    
    Args:
        subtotal (Decimal): Сумма без налогов
        tax_rate (Decimal): Ставка налога в процентах
        service_charge (Decimal): Сервисный сбор в процентах
        
    Returns:
        dict: Детали расчета
    """
    from decimal import Decimal
    
    subtotal = Decimal(str(subtotal))
    tax_rate = Decimal(str(tax_rate))
    service_charge = Decimal(str(service_charge))
    
    tax_amount = subtotal * (tax_rate / 100)
    service_amount = subtotal * (service_charge / 100)
    total = subtotal + tax_amount + service_amount
    
    return {
        'subtotal': subtotal,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'service_charge': service_charge,
        'service_amount': service_amount,
        'total': total
    }


class FileUploadHandler:
    """
    Класс для безопасной обработки загрузки файлов
    """
    
    def __init__(self, allowed_types=None, max_size=None):
        self.allowed_types = allowed_types or ['image/jpeg', 'image/png', 'image/gif']
        self.max_size = max_size or 5 * 1024 * 1024  # 5MB
    
    def validate(self, file):
        """Валидация файла"""
        if file.size > self.max_size:
            raise ValidationError(f'Файл слишком большой. Максимум: {self.max_size / (1024*1024):.1f}MB')
        
        if file.content_type not in self.allowed_types:
            raise ValidationError(f'Недопустимый тип файла: {file.content_type}')
    
    def process(self, file):
        """Обработка файла"""
        self.validate(file)
        
        # Для изображений применяем дополнительную обработку
        if file.content_type.startswith('image/'):
            validate_image_file(file)
            return resize_image(file)

        return file


class UniqueFilenameStorage(FileSystemStorage):
    """
    Кастомное хранилище, которое генерирует уникальные короткие имена файлов
    """

    def get_valid_filename(self, name):
        """
        Возвращает валидное имя файла с уникальным префиксом
        """
        # Получаем директорию и имя файла
        dir_name = os.path.dirname(name)
        file_name = os.path.basename(name)

        # Генерируем уникальное имя файла
        unique_name = generate_unique_filename(file_name, prefix='upload')

        # Собираем полный путь
        if dir_name:
            return os.path.join(dir_name, unique_name)
        else:
            return unique_name

    def get_available_name(self, name, max_length=None):
        """
        Возвращает доступное имя файла, генерируя уникальное если нужно
        """
        dir_name = os.path.dirname(name)
        file_name = os.path.basename(name)

        # Если имя файла уже уникально, возвращаем его
        if not self.exists(name):
            return name

        # Иначе генерируем новое уникальное имя
        name_without_ext = os.path.splitext(file_name)[0]
        ext = os.path.splitext(file_name)[1]

        # Создаем новое уникальное имя
        unique_name = generate_unique_filename(file_name, prefix='upload')

        if dir_name:
            full_name = os.path.join(dir_name, unique_name)
        else:
            full_name = unique_name

        # Проверяем, что новое имя не превышает max_length
        if max_length and len(full_name) > max_length:
            # Если превышает, создаем еще более короткое имя
            timestamp = timezone.now().strftime('%Y%m%d')
            short_id = secrets.token_hex(4)  # 8 символов вместо 16
            short_name = f"upload_{timestamp}_{short_id}{ext}"

            if dir_name:
                full_name = os.path.join(dir_name, short_name)
            else:
                full_name = short_name

        return full_name 