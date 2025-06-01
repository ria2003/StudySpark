# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from cloudinary.models import CloudinaryField

class User(AbstractUser):
    about_me = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    # Replace ImageField with CloudinaryField
    profile_pic = CloudinaryField('image', default='profile_pics/default.png')
    additional_details_filled = models.BooleanField(default=False)