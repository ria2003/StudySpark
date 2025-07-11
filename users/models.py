# AbstractUser includes all standard fields (username, email, etc.), and lets you add more fields on top of it.
from django.contrib.auth.models import AbstractUser
from django.db import models

# for uploading images directly to Cloudinary cloud storage instead of local storage
from cloudinary.models import CloudinaryField

# custom user model that extends AbstractUser 
class User(AbstractUser):
    about_me = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    profile_pic = CloudinaryField('image', default='profile_pics/default.png')

    # boolean flag to track whether the user has filled in their bio, interests, and profile picture
    additional_details_filled = models.BooleanField(default=False)
