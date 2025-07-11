# context_processors -> used to make certain variables available globally in all templates without having to pass them manually in every render() call
def user_profile(request):
    if request.user.is_authenticated:
        # returns dictionary with current user's profile picture URL so it can be used in any HTML template globally as {{ user_profile_pic }} eg: in navbar
        return {
            'user_profile_pic': request.user.profile_pic.url if request.user.profile_pic else None
        }
    return {'user_profile_pic': None}
    
