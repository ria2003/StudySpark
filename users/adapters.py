# adapters -> hooks that allow you to change the default behavior of Allauth at key points during the authentication process

# Controls social login behavior
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# Controls regular Django account behavior (email login, redirect URLs, etc)
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.models import SocialAccount

# used to stop the social login pipeline and immediately return a redirect (very useful when handling edge cases like email conflicts)
from allauth.core.exceptions import ImmediateHttpResponse

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

# custom adapter that controls default login behaviour
class CustomAccountAdapter(DefaultAccountAdapter):
    # tells where to redirect the user after login
    def get_login_redirect_url(self, request):
        # if user is Google user and hasn't filled additional_details -> redirect to profile completion page
        if request.user.is_authenticated and not request.user.additional_details_filled and SocialAccount.objects.filter(user=request.user).exists():
            return '/users/complete_google_profile/'
        # else redirect to home page
        return '/'

# Django's AllAuth Flow: pre_social_login -> new_user -> save_ser -> login

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    # sociallogin -> object that contains all information Allauth receives from a social provider during login or signup
    def is_auto_signup_allowed(self, request, sociallogin):
        # allows auto account creation when someone logs in via Google
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
                    # Force redirect to login page, stopping Allauth’s process
                    raise ImmediateHttpResponse(redirect('login'))
            except User.DoesNotExist:
                # No user with this email, proceed with social login
                pass

        # let AllAuth continue its default behaviour
        return super().pre_social_login(request, sociallogin)
        
    # called when new user is created and mark as additional_details_filled = False so they’ll be redirected to complete their profile.
    def new_user(self, request, sociallogin):
        user = super().new_user(request, sociallogin)
        user.additional_details_filled = False
        return user

    # called everytime even when user already exists unlike new_user
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not sociallogin.is_existing:
            user.additional_details_filled = False
            user.save()
        return user

    # after connecting a social account, redirect to complete profile
    def get_connect_redirect_url(self, request, socialaccount):
        return '/users/complete_google_profile/'
