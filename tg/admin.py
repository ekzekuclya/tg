from django.contrib import admin
from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramAdmin(admin.ModelAdmin):
    list_display = ['username']
