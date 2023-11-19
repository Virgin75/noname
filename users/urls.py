from django.urls import path

from users.views import (
    CreateCompanyView,
    LoginView,
    LogoutView,
    SignUpView,
    UpdateCompanyView,
)

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("create-company/", CreateCompanyView.as_view(), name="create_company"),
    path("update-company/", UpdateCompanyView.as_view(), name="update_company"),
]
