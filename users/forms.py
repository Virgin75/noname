from django import forms
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import Account, Company


class AuthForm(AuthenticationForm):
    """Form used on login page to authenticate users."""

    username = forms.CharField(widget=forms.TextInput(attrs={"class": "input input-bordered input-primary w-full"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input input-bordered input-primary w-full"}))


class ResetPasswordForm(forms.Form):
    """Form used on Reset Password page."""

    password_1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input input-bordered input-primary w-full"}),
        label="Password",
    )
    password_2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input input-bordered input-primary w-full"}),
        label="Confirm password",
    )

    def clean_password_1(self) -> str:
        """Check if the password is at least 8 characters long."""
        password = self.cleaned_data.get("password_1")
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password

    def clean_password_2(self) -> str:
        """Check if the password is at least 8 characters long."""
        password = self.cleaned_data.get("password_2")
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password


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


class UserUpdateForm(forms.ModelForm):
    """Form used to update an existing User instance."""

    class Meta:
        model = Account
        fields = ["email", "first_name", "last_name"]


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
        is_first_creation = not self.instance.pk
        company = super().save(commit=True)
        if is_first_creation:
            self.request.user.company = company
            self.request.user.save()
            self.request.user.set_admin_permissions()
            company.set_basic_custom_fields()
        return company
