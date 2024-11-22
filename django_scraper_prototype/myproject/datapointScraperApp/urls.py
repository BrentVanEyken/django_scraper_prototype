from django.urls import path
from . import views

urlpatterns = [
    path('', views.OverviewDashboardView.as_view(), name='home'),  # Homepage
    path('register/', views.register, name='register'),
    path('settings/', views.user_settings, name='user-settings'),

    path('datapoints/create/', views.DatapointCreateView.as_view(), name='datapoint-create'),
    path('datapoints/', views.DatapointListView.as_view(), name='datapoint-list'),
    path('datapoints/<int:datapoint_id>/scrape/', views.ScrapeDatapointView.as_view(), name='scrape_datapoint'),
    path('datagroups/<int:datagroup_id>/scrape/', views.ScrapeDataGroupView.as_view(), name='scrape_datagroup'),
    path('organisations/<int:organisation_id>/scrape/', views.ScrapeOrganizationView.as_view(), name='scrape_organisation'),
    path('datapoints/scrape_all/', views.ScrapeAllDatapointsView.as_view(), name='scrape_all_datapoints'),
    path('test-xpath/', views.TestXPathView.as_view(), name='test_xpath'),

    path('datapoints/detail/<int:pk>/', views.datapoint_detail, name='datapoint-detail'),
    path('datapoints/edit/<int:pk>/', views.datapoint_edit, name='datapoint-edit'),
    path('datapoints/verify/<int:pk>/', views.datapoint_verify, name='datapoint-verify'),
    path('datapoints/delete/<int:pk>/', views.datapoint_delete, name='datapoint-delete'),
    path('datapoints/revert/<int:pk>/', views.datapoint_revert, name='datapoint-revert'),
]