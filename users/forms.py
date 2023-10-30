from django import forms
from users.models import Account, Company
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login


class AuthForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'input input-bordered input-primary w-full max-w-xs'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered input-primary w-full max-w-xs'}))


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input input-bordered input-primary w-full max-w-xs'}))

    class Meta:
        model = Account
        fields = ['email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save()
        login(self.request, user)
        return user


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'city', 'country']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        company = super().save(commit=True)
        self.request.user.company = company
        self.request.user.save()
        return company
