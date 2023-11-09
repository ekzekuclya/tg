from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import TelegramUser, Payment, Chat


@receiver(pre_delete, sender=TelegramUser)
def delete_payments(sender, instance, **kwargs):
    if instance.is_admin:
        Payment.objects.filter(operator=instance).delete()
        Chat.objects.filter(operator=instance).delete()
