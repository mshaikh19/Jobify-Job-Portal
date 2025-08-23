from django import template

register = template.Library()

@register.filter
def is_http(value):
    # Ensure that the value is a string and starts with http:// or https://
    if isinstance(value, str):
        return value.lower().startswith(('http://', 'https://'))
    return False


@register.filter
def simple_filter(value):
    return "Test Passed"
