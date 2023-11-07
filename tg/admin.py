from django.contrib import admin
from .models import TelegramUser, Chat, Exchange, CurrentUsdtCourse, TGMessage


@admin.register(TGMessage)
class TGMessageAdmin(admin.ModelAdmin):
    list_display = ['sender']


@admin.register(TelegramUser)
class TelegramAdmin(admin.ModelAdmin):
    list_display = ['username', 'is_admin']
    list_filter = ['is_admin']


@admin.register(Chat)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id']
    list_filter = ['is_active']


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ['crypto']
#
#
# @admin.register(CurrentUsdtCourse)
# class CurrentUsdtCourseAdmin(admin.ModelAdmin):
#     list_display = ['usdt']