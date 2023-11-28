from django.forms import CheckboxInput


class CheckboxInputError(CheckboxInput):
    input_type = "checkbox"
    template_name = "django/forms/widgets/checkbox_red.html"
