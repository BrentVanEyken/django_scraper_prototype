from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    column_preferences = models.JSONField(default=dict, blank=True)
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Organization(models.Model):
    """
    Represents an organization that owns Datapoints and DataGroups.
    """
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        permissions = [
            ("can_scrape_organisation", "Can scrape all Datapoints/Datagroups in an Organization"),
        ]
    
    def __str__(self):
        return self.name

class DataGroup(models.Model):
    """
    Optional model to group multiple Datapoints.
    Now associated with an Organization.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='datagroups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "DataGroup"
        verbose_name_plural = "DataGroups"
        permissions = [
            ("can_scrape_datagroup", "Can scrape a specific DataGroup"),
        ]

    def __str__(self):
        return self.name

class Datapoint(models.Model):
    """
    Represents a single scraped data point.
    Now associated with an Organization.
    """
    STATUS_AUTO = 'AUTO'
    STATUS_MANUAL = 'MANUAL'
    STATUS_VERIFY = 'VERIFY'
    STATUS_FIX = 'FIX'

    STATUS_CHOICES = [
        (STATUS_AUTO, 'Automated'),
        (STATUS_MANUAL, 'Manual'),
        (STATUS_VERIFY, 'Verification Required'),
        (STATUS_FIX, 'Fix Needed'),
    ]

    DATA_TYPE_CHOICES = [
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('FLOAT', 'Float'),
        ('DATE', 'Date'),
        ('BOOLEAN', 'Boolean'),
        # Add more data types as needed
    ]

    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    xpath = models.CharField(max_length=500)
    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES)
    previously_verified_data = models.TextField(blank=True, null=True)
    current_verified_data = models.TextField(blank=True, null=True)
    current_unverified_data = models.TextField(blank=True, null=True)
    last_verified = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_AUTO)
    data_group = models.ForeignKey(
        'DataGroup',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='datapoints'
    )
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='datapoints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Datapoint"
        verbose_name_plural = "Datapoints"
        ordering = ['-created_at']
        permissions = [
            ("can_scrape_datapoint", "Can scrape a specific Datapoint"),
            ("can_scrape_all_datapoints", "Can scrape all Datapoints"),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"