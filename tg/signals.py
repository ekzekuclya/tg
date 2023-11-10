from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from .models import TelegramUser, Payment, Chat


@receiver(pre_save, sender=TelegramUser)
def delete_payments(sender, instance, **kwargs):
    if not instance.is_admin:
        Payment.objects.filter(operator=instance).delete()
        Chat.objects.filter(operator=instance).delete()
