from django import forms 
from django.contrib.auth.forms import UserCreationForm 
from .models import User

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

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 
                  'first_name', 'last_name', 'about_me', 'profile_pic']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.interests = ','.join(self.cleaned_data.get('interests', []))
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)