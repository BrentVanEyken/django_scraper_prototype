# myapp/models.py

from django.db import models
from django.utils import timezone

class Organization(models.Model):
    """
    Represents an organization that owns Datapoints and DataGroups.
    """
    name = models.CharField(max_length=255, unique=True)
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['name']
    
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
        verbose_name = "Data Group"
        verbose_name_plural = "Data Groups"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Datapoint(models.Model):
    """
    Represents a single scraped data point.
    Now associated with an Organization.
    """
    STATUS_CHOICES = [
        ('AUTO', 'Automated'),
        ('MANUAL', 'Manual'),
        ('VERIFY', 'Verification Required'),
        ('FIX', 'Fix Needed'),
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AUTO')
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
    
    def __str__(self):
        return f"{self.name} ({self.status})"