# Generated by Django 4.2.7 on 2023-11-07 20:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0018_currentusdtcourse_coms_exchange_operator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tgmessage',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg.telegramuser'),
        ),
    ]
