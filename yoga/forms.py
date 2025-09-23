from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Practice

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username','first_name','last_name','email','password1','password2')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio','avatar')

class PracticeForm(forms.ModelForm):
    class Meta:
        model = Practice
        fields = ('date','poses','duration_minutes','notes')
        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
            'poses': forms.CheckboxSelectMultiple(),
        }
