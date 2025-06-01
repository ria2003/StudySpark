from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_authenticated and not request.user.additional_details_filled and SocialAccount.objects.filter(user=request.user).exists():
            return '/users/complete_google_profile/'
        return '/'

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        # Auto signup is allowed, but we'll mark the user as needing to complete profile
        return True
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        """
        # Get the email from the sociallogin object
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
        
        if email:
            # Check if a user exists with this email and doesn't have a social account
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                # Check if this user doesn't have a social account
                if not SocialAccount.objects.filter(user=user, provider=sociallogin.account.provider).exists():
                    # This email is already used for a regular account
                    messages.error(
                        request,
                        "An account already exists with this email address. Please log in with your username and password."
                    )
                    # Redirect to login page
                    raise ImmediateHttpResponse(redirect('login'))
            except User.DoesNotExist:
                # No user with this email, proceed with social login
                pass
        
        return super().pre_social_login(request, sociallogin)
        
    def new_user(self, request, sociallogin):
        user = super().new_user(request, sociallogin)
        user.additional_details_filled = False
        return user
        
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.additional_details_filled = False
        user.save()
        return user
        
    def get_connect_redirect_url(self, request, socialaccount):
        # After connecting a social account, redirect to complete profile
        return '/users/complete_google_profile/'