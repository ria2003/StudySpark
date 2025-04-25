from django.conf import settings
from . import views 
from django.urls import path
from django.conf.urls.static import static
from .views import (
    CustomPasswordResetView, 
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView
)

urlpatterns = [
    path('signup/', views.register, name='register'),
    path('signin/', views.user_login, name='login'),
    path('complete_google_profile/', views.complete_google_profile, name='complete_google_profile'),
    path('logout/', views.user_logout, name='logout'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
