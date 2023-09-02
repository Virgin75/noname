from django.urls import path
from commons.views import HomeView

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
]
