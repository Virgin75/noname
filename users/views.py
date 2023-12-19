from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import BaseUpdateView, CreateView, FormView, UpdateView

from users.forms import AuthForm, CompanyForm, UserRegisterForm
from users.models import Account


class SignUpView(SuccessMessageMixin, CreateView):
    template_name = "users/signup.html"
    success_url = reverse_lazy("users:create_company")
    form_class = UserRegisterForm
    success_message = "Your profile was created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = AuthForm

    def get(self, request, *args, **kwargs):
        if isinstance(request.user, AnonymousUser):
            return super().get(request, *args, **kwargs)
        return redirect(reverse_lazy("commons:home"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages"] = messages.get_messages(self.request)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return self.form_valid(form)
        else:
            print("in else")
            messages.error(request, "error")
            return self.form_invalid(form)

    def get_success_url(self):
        user = Account.objects.get(email=self.get_form_kwargs().get("data").get("username"))
        return reverse_lazy("commons:home") if user.company else reverse_lazy("users:create_company")


class LogoutView(TemplateView):
    template_name = "users/logout.html"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class CreateCompanyView(SuccessMessageMixin, CreateView, LoginRequiredMixin):
    template_name = "users/create_company.html"
    success_url = reverse_lazy("commons:home")
    form_class = CompanyForm
    success_message = "Company created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class UpdateCompanyView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    template_name = "users/company_details.html"
    success_message = "Company updated successfully."
    success_url = reverse_lazy("users:update_company")
    form_class = CompanyForm

    def get_object(self, **kwargs):
        return self.request.user.company

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class ListCompanyMembersView(ListView, LoginRequiredMixin):
    """View used to retrieve all the Company members."""
    template_name = "users/list_company_members.html"
    paginate_by = 10

    def get_queryset(self):
        return Account.objects.filter(company=self.request.user.company).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = self.request.user.company
        context["fields"] = ["", "Name", "Email", "Creation date", "Permissions", ""]
        print(context)
        return context



class UpdateAccountView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update the user's Account details."""

    template_name = "users/update_account.html"
    success_message = "Your profile was updated successfully."
    success_url = reverse_lazy("users:update_account")
    form_class = UserRegisterForm

    def get_object(self, **kwargs):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
