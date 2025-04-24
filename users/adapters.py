from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if not request.user.additional_details_filled and SocialAccount.objects.filter(user=request.user).exists():
            return '/users/complete_google_profile/'
        return '/'

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        return True  # Skip the intermediate signup form
        
    def new_user(self, request, sociallogin):
        user = super().new_user(request, sociallogin)
        user.additional_details_filled = False
        return user
        
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.additional_details_filled:
            user.additional_details_filled = False
            user.save()
        return user