from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Основные компоненты'

    def ready(self):
        """
        Импортируем сигналы при инициализации приложения
        """
        import core.signals
