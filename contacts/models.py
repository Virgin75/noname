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


class Segment(HistoryMixin):
    """
    A Segment is a group of Contacts sharing some specific characteristics.

    Segment members are dynamically computed every 30mn. depending on chosen 'filters'.
    Details on the 'filters' attribute:
     - list of dictionaries
     - each dict has:
        > an 'operator' key with value 'AND' or 'OR'
        > a 'filters' key with key/value pairs on which to filter Contacts
    """
    name = models.CharField(max_length=50)
    description = models.TextField()
    belongs_to = models.ForeignKey('users.Company', on_delete=models.CASCADE, null=True, blank=True)
    members = models.ManyToManyField(Contact, related_name='segments')

    def __str__(self):
        return self.name

    @property
    def members_count(self):
        return self.members.count()


class Filter(models.Model):
    """Filter used to create a Segment."""
    FILTERS = (
        ('email', 'Email'),
        ('fields', 'Custom field'),
    )
    filter_type = models.CharField(max_length=20, choices=FILTERS, default=FILTERS[0][0])
    comparator = models.CharField(max_length=20, choices=(('eq', 'equals'), ('neq', 'not equals')), default='eq')
    value = models.CharField(max_length=100, blank=True, null=True)
    belongs_to = models.ForeignKey('users.Company', on_delete=models.CASCADE, null=True, blank=True)


class Group(models.Model):
    """Group of Filters that will be chained with an 'operator' (AND, OR) to create a Segment."""
    operator = models.CharField(max_length=3, choices=(('AND', 'all'), ('OR', 'any')), default='AND')
    filters = models.ManyToManyField("Filter", related_name='groups')
    belongs_to = models.ForeignKey('users.Company', on_delete=models.CASCADE, null=True, blank=True)
    segment = models.OneToOneField(Segment, on_delete=models.CASCADE, related_name='groups', null=True, blank=True)
