from django.conf import settings
from . import views 
from django.urls import path
from django.conf.urls.static import static

urlpatterns = [
    path('signup/', views.register, name='register'),
    path('signin/', views.user_login, name='login'),
    path('complete_google_profile/', views.complete_google_profile, name='complete_google_profile'),
    path('logout/', views.user_logout, name='logout'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
