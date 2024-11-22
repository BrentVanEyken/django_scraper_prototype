from django import template

from datapointScraperApp.models import Datapoint, Organization

register = template.Library()

@register.filter
def display_data_group(data_group):
    if data_group:
        return data_group.name
    return 'N/A'

@register.filter
def get_organization_name(organizations, org_id):
    """
    Given a list of organizations and an organization ID, return the organization's name.
    """
    for org in organizations:
        if str(org.id) == str(org_id):
            return org.name
    return 'Unknown Organization'

@register.filter
def get_status_display(status_code):
    status_mapping = {
        'AUTO': 'Automated',
        'MANUAL': 'Manual',
        'VERIFY': 'Verification',
        'FIX': 'Fix Needed',
    }
    return status_mapping.get(status_code, 'Unknown Status')