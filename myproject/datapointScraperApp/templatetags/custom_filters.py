from django import template

register = template.Library()

@register.filter
def display_data_group(data_group):
    if data_group:
        return data_group.name
    return 'N/A'
