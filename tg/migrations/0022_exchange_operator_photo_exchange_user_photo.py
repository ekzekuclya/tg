# Generated by Django 4.2.7 on 2023-11-07 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0021_alter_telegramuser_options_alter_tgmessage_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchange',
            name='operator_photo',
            field=models.CharField(blank=True, max_length=2555, null=True),
        ),
        migrations.AddField(
            model_name='exchange',
            name='user_photo',
            field=models.CharField(blank=True, max_length=2555, null=True),
        ),
    ]
