# Generated by Django 4.2.7 on 2023-11-10 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0028_telegramuser_referred_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='balance',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
