# Generated by Django 5.2 on 2025-05-19 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Citoyen', '0005_alter_notification_options_remove_notification_data_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]
