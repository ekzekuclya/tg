# Generated by Django 4.2.7 on 2023-11-09 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0025_alter_payment_mbank_alter_payment_optima'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='coms',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payment',
            name='usdt',
            field=models.FloatField(default=2),
            preserve_default=False,
        ),
    ]