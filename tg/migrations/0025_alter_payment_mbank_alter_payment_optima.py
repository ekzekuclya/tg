# Generated by Django 4.2.7 on 2023-11-08 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0024_payment_operator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='mbank',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='optima',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
