# Generated by Django 5.1.5 on 2025-02-05 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_profile_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_pic',
            field=models.ImageField(default='profile_pics/default.png', upload_to='profile_pics/'),
        ),
    ]
