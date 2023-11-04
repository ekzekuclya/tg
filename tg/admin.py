from django.contrib import admin
from .models import TelegramUser, Order


@admin.register(TelegramUser)
class TelegramAdmin(admin.ModelAdmin):
    list_display = ['username']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id']
