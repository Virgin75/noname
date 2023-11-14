from django.forms.widgets import Input


class SearchInput(Input):
    input_type = "text"
    template_name = "django/forms/widgets/search.html"
