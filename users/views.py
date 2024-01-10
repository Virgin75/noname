from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import BaseUpdateView, CreateView, FormView, UpdateView

from users.forms import AuthForm, CompanyForm, UserRegisterForm, UserUpdateForm
from users.models import Account


class SignUpView(SuccessMessageMixin, CreateView):
    """View used to register new users."""

    template_name = "users/signup.html"
    success_url = reverse_lazy("users:create_company")
    form_class = UserRegisterForm
    success_message = "Your profile was created successfully."

    def get_form_kwargs(self):
        """Pass the current request to the form kwargs in order to allow authentication upon user creation."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class LoginView(FormView):
    """View used to authenticate users."""

    template_name = "users/login.html"
    form_class = AuthForm

    def get(self, request, *args, **kwargs):
        """If the user is already authenticated, redirect him to the home page."""
        if isinstance(request.user, AnonymousUser):
            return super().get(request, *args, **kwargs)
        return redirect(reverse_lazy("commons:home"))

    def get_context_data(self, **kwargs):
        """Pass the messages to the context in order to display them on the page."""
        context = super().get_context_data(**kwargs)
        context["messages"] = messages.get_messages(self.request)
        return context

    def post(self, request, *args, **kwargs):
        """If the form is valid, log the user in. Otherwise, display an error message."""
        form = self.get_form()
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return self.form_valid(form)
        else:
            messages.error(request, "error")
            return self.form_invalid(form)

    def get_success_url(self):
        """If the user already has a Company, redirect to home page. Else, redirect him to the Company creation page."""
        user = Account.objects.get(email=self.get_form_kwargs().get("data").get("username"))
        return reverse_lazy("commons:home") if user.company else reverse_lazy("users:create_company")


class LogoutView(TemplateView):
    """View used to log the user out."""

    template_name = "users/logout.html"

    def get(self, request, *args, **kwargs):
        """Log the user out and redirect him to the logged out page."""
        logout(request)
        return super().get(request, *args, **kwargs)


class CreateCompanyView(SuccessMessageMixin, CreateView, LoginRequiredMixin):
    """View used to create a new Company."""

    template_name = "users/create_company.html"
    success_url = reverse_lazy("commons:home")
    form_class = CompanyForm
    success_message = "Company created successfully."

    def get_form_kwargs(self):
        """Pass the current request to the form kwargs in order to set current user's Company to the one created."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class UpdateCompanyView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update the user's Company details."""

    template_name = "users/company_details.html"
    success_message = "Company updated successfully."
    success_url = reverse_lazy("users:update_company")
    form_class = CompanyForm

    def get_object(self, **kwargs):
        """Only return the current user's Company."""
        return self.request.user.company

    def get_form_kwargs(self):
        """Pass the current request to the form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class ListCompanyMembersView(ListView, LoginRequiredMixin):
    """View used to retrieve all the Company members."""

    template_name = "users/list_company_members.html"
    paginate_by = 10

    def get_queryset(self):
        """Only return the users belonging to the current user's Company."""
        return Account.objects.filter(company=self.request.user.company).order_by("-id")

    def get_context_data(self, **kwargs):
        """Add the Company and the fields to the context data (used in html)."""
        context = super().get_context_data(**kwargs)
        context["company"] = self.request.user.company
        context["fields"] = ["", "Name", "Email", "Creation date", "Permissions", ""]
        return context


class UpdateAccountView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update the user's Account details."""

    template_name = "users/update_account.html"
    success_message = "Your profile was updated successfully."
    success_url = reverse_lazy("users:update_account")
    form_class = UserUpdateForm

    def get_object(self, **kwargs):
        """Only allow the user to update his own Account."""
        return self.request.user

    def get_form_kwargs(self):
        """Pass request to the form kwargs in order to allow re-authentication upon user update."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class AddUserPermissionView(UpdateView, LoginRequiredMixin):
    """View used to add a permission to a user (HTMX)."""

    def post(self, request, *args, **kwargs):
        """Add the chosen permission to the User instance."""
        try:
            user = Account.objects.get(id=kwargs.get("user_id"), company=request.user.company)
            perm_group = list(request.POST.keys())[0]
            chosen_perm = list(request.POST.values())[0]
            user_perms = user.user_permissions.filter(codename__startswith=perm_group)
            if perm_group not in ("extra_can_export", "extra_company_admin"):
                # Uniselect
                for perm in user_perms:
                    user.user_permissions.remove(perm)
                if chosen_perm != "null":
                    user.user_permissions.add(Permission.objects.get(codename=chosen_perm))
            else:
                # Multiselect
                if chosen_perm == "yes":
                    user.user_permissions.add(Permission.objects.get(codename=perm_group))
                else:
                    user.user_permissions.remove(Permission.objects.get(codename=perm_group))

            cache.delete(f"perms_{user.id}")
        except Account.DoesNotExist:
            return HttpResponse(status=404)
        return HttpResponse(status=200)
