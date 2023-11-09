from django.apps import AppConfig


class TgConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tg'

    def ready(self):
        import tg.signals
