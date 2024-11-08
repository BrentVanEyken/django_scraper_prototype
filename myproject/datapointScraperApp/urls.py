from django.urls import path
from . import views

urlpatterns = [
    path('', views.OverviewDashboardView.as_view(), name='home'),  # Homepage
    path('register/', views.register, name='register'),
    path('datapoints/create/', views.DatapointCreateView.as_view(), name='datapoint-create'),
    path('datapoints/', views.DatapointListView.as_view(), name='datapoint-list'),
    path('datapoints/<int:pk>/', views.DatapointDetailView.as_view(), name='datapoint-detail'),
    path('datapoints/<int:pk>/edit/', views.DatapointUpdateView.as_view(), name='datapoint-update'),
    path('datapoints/<int:pk>/delete/', views.DatapointDeleteView.as_view(), name='datapoint-delete'),
    path('datapoints/<int:datapoint_id>/scrape/', views.ScrapeDatapointView.as_view(), name='scrape_datapoint'),
    path('datagroups/<int:datagroup_id>/scrape/', views.ScrapeDataGroupView.as_view(), name='scrape_datagroup'),
    path('organisations/<int:organisation_id>/scrape/', views.ScrapeOrganizationView.as_view(), name='scrape_organisation'),
    path('datapoints/scrape_all/', views.ScrapeAllDatapointsView.as_view(), name='scrape_all_datapoints'),
]