import secrets

from django.db import models


class TelegramUser(models.Model):
    user_id = models.IntegerField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    referred_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    balance = models.PositiveIntegerField(default=0)
    operator_balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.username if self.username else "None"

    class Meta:
        ordering = ['-last_activity']


class Chat(models.Model):
    operator = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="oper",
                                 default=None)
    user = models.ManyToManyField(TelegramUser, blank=True, related_name="user")
    is_active = models.BooleanField(default=True)


class Exchange(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    operator = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="operator")
    amount = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    crypto = models.CharField(max_length=25, null=True)
    kgs_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user_photo = models.CharField(max_length=2555, null=True, blank=True)
    operator_photo = models.CharField(max_length=2555, null=True, blank=True)
    balance_used = models.IntegerField(default=None, null=True, blank=True)


class CurrentUsdtCourse(models.Model):
    usdt = models.FloatField()
    coms = models.IntegerField()


class TGMessage(models.Model):
    order = models.ForeignKey(Chat, on_delete=models.SET_NULL, related_name="messages", null=True, blank=True)
    message_id = models.IntegerField(unique=True)
    sender = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    operator = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    mbank = models.CharField(max_length=255, null=True, blank=True)
    optima = models.CharField(max_length=255, null=True, blank=True)
    usdt = models.FloatField(null=True, blank=True)
    coms = models.IntegerField(null=True, blank=True)


class Promo(models.Model):
    promo_text = models.CharField(max_length=5, unique=True)
    amount = models.PositiveIntegerField()
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.promo_text = secrets.token_urlsafe(5)
        while Promo.objects.filter(promo_text=self.promo_text).exists():
            self.promo_text = secrets.token_urlsafe(5)
        super().save(*args, **kwargs)
