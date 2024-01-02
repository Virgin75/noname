from django import forms
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import Account, Company


class AuthForm(AuthenticationForm):
    """Form used on login page to authenticate users."""

    username = forms.CharField(widget=forms.TextInput(attrs={"class": "input input-bordered input-primary w-full"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input input-bordered input-primary w-full"}))


class UserRegisterForm(UserCreationForm):
    """Form used on register page to create new users."""

    class Meta:
        model = Account
        fields = ["email", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the user and log him in just after."""
        user = super().save()
        login(self.request, user)
        return user


class CompanyForm(forms.ModelForm):
    """Form used on Company creation page (just after 1st login), also used to edit a Company details."""

    class Meta:
        model = Company
        fields = ["name", "address", "city", "country"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """When the Company is created, set the user's company to this one. Then save the user."""
        company = super().save(commit=True)
        self.request.user.company = company
        self.request.user.save()
        return company
