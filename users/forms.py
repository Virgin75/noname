from django import forms
from users.models import Account, Company
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

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
