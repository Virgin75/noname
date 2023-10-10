from django.urls import path
from contacts.views import ListContact

urlpatterns = [
    path('contacts/', ListContact.as_view(), name='list_contacts'),
]
