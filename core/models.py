import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    Абстрактная модель с полями created_at и updated_at
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Абстрактная модель с UUID полем как первичным ключом
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, UUIDModel):
    """
    Базовая модель, объединяющая UUID и временные метки
    """
    class Meta:
        abstract = True
