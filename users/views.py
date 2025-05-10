# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

from .forms import UserRegistrationForm
from .models import User
import logging
import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required



logger = logging.getLogger(__name__)

# Custom Password Reset View that filters out Google-authenticated users
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        # Check if this email belongs to a Google-authenticated user
        social_user = SocialAccount.objects.filter(user__email=email, provider='google').exists()
        
        if social_user:
            # Add an error to the form if the user is authenticated via Google
            form.add_error('email', 'This email is registered via Google. Please use Google Sign-In instead.')
            return self.form_invalid(form)
        
        return super().form_valid(form)

# Standard password reset views with custom templates
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

# Add a decorator to check if profile is complete
def profile_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check if user has completed additional details
            if not request.user.additional_details_filled:
                social_account = SocialAccount.objects.filter(user=request.user).first()
                if social_account:
                    messages.warning(request, 'Please complete your profile before continuing.')
                    return redirect('complete_google_profile')
                else:
                    # If it's not a social account but somehow additional_details_filled is False
                    request.user.additional_details_filled = True
                    request.user.save()
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return _wrapped_view


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        try:
            # Log form data (exclude passwords)
            form_data = {k: v for k, v in request.POST.items() if 'password' not in k}
            logger.info(f"Form data received: {form_data}")
            
            if form.is_valid():
                # Create user using the form's save method which handles interests properly
                user = form.save()
                user.additional_details_filled = True  # Set to True for regular signups
                user.save()
                logger.info(f"User {user.username} created successfully")
                
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')  # Redirect to login after signup
            else:
                # Log form errors
                logger.error(f"Form validation errors: {form.errors}")
                # Form errors will be displayed in the template
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            messages.error(request, f"Error creating account: {str(e)}")
    else:
        # GET request - create empty form
        form = UserRegistrationForm()
        
    # Pass the form instance to the template
    return render(request, 'users/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        logger.info("Received POST request for login")
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            remember_me = request.POST.get('remember_me')
            
            logger.info(f"Attempting login for user: {username}")
            user = authenticate(username=username, password=password)
            
            if user:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                logger.info(f"User {username} logged in successfully")
                
                # Check if user has completed additional details
                if not user.additional_details_filled:
                    social_account = SocialAccount.objects.filter(user=user).first()
                    if social_account:
                        return redirect('complete_google_profile')
                
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                logger.error(f"Invalid login attempt for user: {username}")
                messages.error(request, 'Invalid credentials')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messages.error(request, f"Login error: {str(e)}")
            
    return render(request, 'users/signin.html', {'profile_pic_url': request.user.profile_pic.url if request.user.is_authenticated else None})

# Google login handler - this is called after successful Google authentication
def google_login(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    social_account = SocialAccount.objects.filter(user=request.user).first()
    if social_account and not request.user.additional_details_filled:
        messages.info(request, 'Please complete your profile to continue.')
        return redirect('complete_google_profile')
        
    return redirect('home')

@login_required
def complete_google_profile(request):
    # Redirect non-Google users or users who already completed their profile
    social_account = SocialAccount.objects.filter(user=request.user).first()
    if not social_account:
        messages.warning(request, 'This page is only for Google users.')
        return redirect('home')
        
    if request.user.additional_details_filled:
        messages.info(request, 'Your profile is already complete.')
        return redirect('home')
    
    if request.method == 'POST':
        user = request.user
        
        # Save about_me to the user model
        user.about_me = request.POST.get('about_me')
        
        # Handle interests
        interests = request.POST.getlist('interests')
        user.interests = ','.join(interests)
        
        # Handle profile picture
        if 'profile_pic' in request.FILES:
            user.profile_pic = request.FILES['profile_pic']
        elif social_account and social_account.extra_data.get('picture'):
            # Download and save Google profile picture if no custom upload
            profile_pic_url = social_account.extra_data.get('picture')
            response = requests.get(profile_pic_url)
            if response.status_code == 200:
                user.profile_pic.save(
                    f'google_profile_{user.username}.jpg', 
                    ContentFile(response.content)
                )
        
        user.additional_details_filled = True
        user.save()
        messages.success(request, 'Profile completed successfully!')
        return redirect('home')
    
    # Pre-fill email and other fields from Google account
    initial_email = social_account.extra_data.get('email') if social_account else ''
    initial_first_name = social_account.extra_data.get('given_name') if social_account else ''
    initial_last_name = social_account.extra_data.get('family_name') if social_account else ''
    initial_username = social_account.extra_data.get('email', '').split('@')[0] if social_account else ''
    
    context = {
        'initial_email': initial_email,
        'initial_first_name': initial_first_name,
        'initial_last_name': initial_last_name,
        'initial_username': initial_username,
        'profile_pic_url': social_account.extra_data.get('picture') if social_account else None
    }
    return render(request, 'users/complete_google_profile.html', context)


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

