from users.forms import UserRegisterForm, CompanyForm
from users.models import Account
from django.views.generic.edit import CreateView, FormView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.forms import AuthenticationForm


class SignUpView(SuccessMessageMixin, CreateView):
    template_name = 'users/signup.html'
    success_url = reverse_lazy('create_company')
    form_class = UserRegisterForm
    success_message = "Your profile was created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class LoginView(FormView):
    template_name = 'users/login.html'
    form_class = AuthenticationForm

    def get_success_url(self):
        user = Account.objects.get(email=self.get_form_kwargs().get('data').get('username'))
        return reverse_lazy('home') if user.company else reverse_lazy('create_company')


class LogoutView(TemplateView):
    template_name = 'users/logout.html'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class CreateCompanyView(SuccessMessageMixin, CreateView):
    template_name = 'users/create_company.html'
    success_url = reverse_lazy('home')
    form_class = CompanyForm
    success_message = "Company created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
