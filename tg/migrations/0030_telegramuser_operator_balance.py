# Generated by Django 4.2.7 on 2023-11-10 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0029_telegramuser_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='operator_balance',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
