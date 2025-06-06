# Generated by Django 5.2 on 2025-05-29 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Citoyen', '0008_user_phone_verified_verificationcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to='problem_documents/', verbose_name='Document'),
        ),
        migrations.AddField(
            model_name='problem',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='problem_videos/', verbose_name='Video'),
        ),
        migrations.AddField(
            model_name='problem',
            name='voice_record',
            field=models.FileField(blank=True, null=True, upload_to='problem_voice/', verbose_name='Voice Record'),
        ),
    ]
