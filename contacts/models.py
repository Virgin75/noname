from django.db import models

from commons.models import HistoryMixin


class Contact(HistoryMixin):
    """
    Stores information on a Contact.

    A Contact is a person that opted-in to receive emails from a Company.
    """
    email = models.EmailField()
    belongs_to = models.ForeignKey('users.Company', on_delete=models.CASCADE, null=True, blank=True)
    fields = models.JSONField(default=dict)

    def __str__(self):
        return self.email


class AllowedField(models.Model):
    """
    List of fields that can be used in the 'fields' attribute of a Contact (per Company).
    """
    ALLOWED_TYPES = (
        ('str', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('bool', 'Boolean'),
    )
    name = models.SlugField(max_length=50)
    type = models.CharField(max_length=20, choices=ALLOWED_TYPES, default=ALLOWED_TYPES[0][0])
    belongs_to = models.ForeignKey('users.Company', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('name', 'belongs_to')

    def __str__(self):
        return self.name
