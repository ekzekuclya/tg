# Generated by Django 4.2.7 on 2023-11-11 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0030_telegramuser_operator_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchange',
            name='balance_used',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]