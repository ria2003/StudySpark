# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    about_me = models.TextField(blank=True)  
    interests = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png')
    additional_details_filled = models.BooleanField(default=False)