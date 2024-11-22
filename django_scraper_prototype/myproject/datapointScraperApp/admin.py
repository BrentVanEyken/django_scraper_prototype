from django.contrib import admin
from .models import Datapoint, DataGroup, Organization, UserProfile

@admin.register(Datapoint)
class DatapointAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'data_type', 'last_verified', 'last_updated')
    list_filter = ('status', 'data_type', 'data_group')
    search_fields = ('name', 'url', 'xpath')
    ordering = ('-created_at',)

@admin.register(DataGroup)
class DataGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

admin.site.register(UserProfile)