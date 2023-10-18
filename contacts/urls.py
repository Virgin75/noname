from django.urls import path
from contacts.views import ListContact, CreateContact

urlpatterns = [
    path('contacts/', ListContact.as_view(), name='list_contacts'),
    path('contacts/add', CreateContact.as_view(), name='create_contact'),
]
