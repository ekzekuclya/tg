# Generated by Django 4.2.7 on 2023-11-04 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0006_telegramuser_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramuser',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
