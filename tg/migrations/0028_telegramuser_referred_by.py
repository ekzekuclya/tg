# Generated by Django 4.2.7 on 2023-11-10 00:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0027_alter_payment_coms_alter_payment_usdt'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='referred_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg.telegramuser'),
        ),
    ]
