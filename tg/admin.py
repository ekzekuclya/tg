from django.contrib import admin
from .models import TelegramUser, Chat, Exchange, CurrentUsdtCourse, TGMessage, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['operator']

@admin.register(TGMessage)
class TGMessageAdmin(admin.ModelAdmin):
    list_display = ['sender']


@admin.register(TelegramUser)
class TelegramAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'is_admin']
    list_filter = ['is_admin']


@admin.register(Chat)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id']
    list_filter = ['is_active']


@admin.register(CurrentUsdtCourse)
class CurrentUsdtCourseAdmin(admin.ModelAdmin):
    list_display = ['usdt', 'coms']


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ['crypto', 'confirmed', 'user.username' if 'user.username' else 'None']
#
#
# @admin.register(CurrentUsdtCourse)
# class CurrentUsdtCourseAdmin(admin.ModelAdmin):
#     list_display = ['usdt']
