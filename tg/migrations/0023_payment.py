# Generated by Django 4.2.7 on 2023-11-07 23:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0022_exchange_operator_photo_exchange_user_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mbank', models.CharField(max_length=255)),
                ('optima', models.CharField(max_length=255)),
            ],
        ),
    ]
