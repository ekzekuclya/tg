# Generated by Django 4.2.7 on 2023-11-04 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0005_alter_order_operator'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]