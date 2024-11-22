from django import template

from datapointScraperApp.models import Organization

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})

@register.filter(name='get_status_count')
def get_status_count(organization, status):
    return getattr(organization, f"{status.lower()}_count", 0)

@register.filter
def get_organization_name(organizations, org_id):
    try:
        org = organizations.get(id=org_id)
        return org.name
    except Organization.DoesNotExist:
        return "Unknown Organization"