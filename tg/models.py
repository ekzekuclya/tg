from django.db import models


class TelegramUser(models.Model):
    user_id = models.IntegerField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username


class Order(models.Model):
    operator = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="oper",
                                 default=None)
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="user")
    is_active = models.BooleanField(default=True)


class Exchange(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    ltc_amount = models.DecimalField(max_digits=10, decimal_places=4)
    kgs_amount = models.DecimalField(max_digits=10, decimal_places=2)
    crypto = 
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - LTC to KGS Exchange"
