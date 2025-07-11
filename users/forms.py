from django import forms 
# built-in registration form with username, password1, and password2.
from django.contrib.auth.forms import UserCreationForm 
from .models import User

# extending UserCreationForm to reuse Django's secure password validation system while adding custom fields
class UserRegistrationForm(UserCreationForm):
    interests = forms.MultipleChoiceField(
        choices=[
            ('science_tech', 'Science & Technology'),
            ('humanities_arts', 'Humanities & Arts'),
            ('business_economy', 'Business & Economy'),
            ('health_lifestyle', 'Health & Lifestyle'),
            ('entertainment_creativity', 'Entertainment & Creativity'),
            ('other', 'Other'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    about_me = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
        required=False
    )

    # Meta connects the form to custom User model and tells Django which fields to render automatically
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 
                  'first_name', 'last_name', 'about_me', 'profile_pic']

    # override the default save() method to manually process the interests field
    #  commit parameter controls whether to immediately save the object to the database
    def save(self, commit=True):
        # commit=False lets you customize the object before saving
        user = super().save(commit=False)
        # saves selected interests as a list of string eg: "science_tech,entertainment_creativity"
        user.interests = ','.join(self.cleaned_data.get('interests', []))
        # commit=True means no further customization 
        if commit:
            user.save()
        return user

# custom login form passed into the authenticate() function in user_login view.
class LoginForm(forms.Form):
    username = forms.CharField()
    # forms.PasswordInput ensures password is shown as •••• instead of plain text
    password = forms.CharField(widget=forms.PasswordInput)
