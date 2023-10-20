from django.urls import path
from contacts.views import ListContact, CreateContact, ListCustomField, CreateCustomField

urlpatterns = [
    path('contacts/', ListContact.as_view(), name='list_contacts'),
    path('contacts/add', CreateContact.as_view(), name='create_contact'),
    path('contacts/fields', ListCustomField.as_view(), name='list_custom_fields'),
    path('contacts/fields/add', CreateCustomField.as_view(), name='create_custom_field'),
]
