from django.urls import path
from users.views import SignUpView, LoginView, CreateCompanyView, LogoutView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('create-company/', CreateCompanyView.as_view(), name='create_company'),
]
