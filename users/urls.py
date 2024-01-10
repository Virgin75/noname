from django.urls import path

from users.views import (
    AddCompanyMemberView,
    AddUserPermissionView,
    CreateCompanyView,
    DeleteCompanyMemberView,
    ListCompanyMembersView,
    LoginView,
    LogoutView,
    ResetPasswordView,
    SignUpView,
    UpdateAccountView,
    UpdateCompanyView,
)

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("create-company/", CreateCompanyView.as_view(), name="create_company"),
    path("update-company/", UpdateCompanyView.as_view(), name="update_company"),
    path("company-members/", ListCompanyMembersView.as_view(), name="company_members"),
    path("delete-member/<int:user_id>/", DeleteCompanyMemberView.as_view(), name="delete_company_member"),
    path("add-member/", AddCompanyMemberView.as_view(), name="add_company_member"),
    path("update-account/", UpdateAccountView.as_view(), name="update_account"),
    path("add-permission/<int:user_id>/", AddUserPermissionView.as_view(), name="add_user_permission"),
    path("reset-password/<int:user_id>/<uuid:token>", ResetPasswordView.as_view(), name="reset_password"),
]
