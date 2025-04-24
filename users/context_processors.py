def user_profile(request):
    if request.user.is_authenticated:
        return {
            'user_profile_pic': request.user.profile_pic.url if request.user.profile_pic else None
        }
    return {'user_profile_pic': None}
    