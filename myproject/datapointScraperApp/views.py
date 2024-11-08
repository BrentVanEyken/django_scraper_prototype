from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.contrib import messages
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import models
from django.db.models import Count, Q

from .forms import RegisterForm, DatapointForm
from .models import Datapoint, Organization, DataGroup
from datetime import datetime

from .tasks import (
    scrape_datapoint_task,
    scrape_datagroup_task,
    scrape_organisation_task,
    scrape_all_datapoints_task
)

@login_required
def home(request):
    current_year = datetime.now().year
    return render(request, 'home.html', {'current_year': current_year})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('home')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = RegisterForm()
    current_year = datetime.now().year
    return render(request, 'registration/register.html', {'form': form, 'current_year': current_year})



class DatapointCreateView(LoginRequiredMixin, CreateView):
    model = Datapoint
    form_class = DatapointForm
    template_name = 'datapoint_create.html' 
    success_url = reverse_lazy('datapoint-list')

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        response = super().form_valid(form)
        return response

class DatapointListView(LoginRequiredMixin, ListView):
    model = Datapoint
    template_name = 'datapoint_list.html'
    context_object_name = 'datapoints'
    paginate_by = 10  # Adjust as needed

class DatapointDetailView(LoginRequiredMixin, DetailView):
    model = Datapoint
    template_name = 'datapoint_detail.html'
    context_object_name = 'datapoint'

class DatapointUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Datapoint
    form_class = DatapointForm
    template_name = 'datapoint_update.html'
    success_url = reverse_lazy('datapoint-list')
    permission_required = 'datapointScraperApp.change_datapoint'

class DatapointDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Datapoint
    template_name = 'datapoint_delete.html'
    success_url = reverse_lazy('datapoint-list')
    permission_required = 'datapointScraperApp.delete_datapoint'

class OverviewDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'overview_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Define the status choices as per your Datapoint model
        status_choices = Datapoint.STATUS_CHOICES  # Now includes class attributes

        # Aggregate the number of Datapoints per status per organization
        organizations = Organization.objects.annotate(
            auto_count=Count('datapoints', filter=Q(datapoints__status=Datapoint.STATUS_AUTO)),
            manual_count=Count('datapoints', filter=Q(datapoints__status=Datapoint.STATUS_MANUAL)),
            verify_count=Count('datapoints', filter=Q(datapoints__status=Datapoint.STATUS_VERIFY)),
            fix_count=Count('datapoints', filter=Q(datapoints__status=Datapoint.STATUS_FIX)),
        )

        # Prepare data for Chart.js
        chart_labels = [org.name for org in organizations]
        auto_counts = [org.auto_count for org in organizations]
        manual_counts = [org.manual_count for org in organizations]
        verify_counts = [org.verify_count for org in organizations]
        fix_counts = [org.fix_count for org in organizations]

        context.update({
            'organizations': organizations,
            'chart_labels': chart_labels,
            'auto_counts': auto_counts,
            'manual_counts': manual_counts,
            'verify_counts': verify_counts,
            'fix_counts': fix_counts,
            'status_choices': status_choices,
        })

        return context
    
class ScrapeDatapointView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View to trigger scraping for a specific Datapoint.
    """
    permission_required = 'datapointScraperApp.can_scrape_datapoint'  # Define appropriate permission

    def post(self, request, datapoint_id):
        datapoint = get_object_or_404(Datapoint, id=datapoint_id)
        if datapoint.status != Datapoint.STATUS_AUTO:
            messages.warning(request, f"Datapoint '{datapoint.name}' is not in 'AUTO' status.")
            return redirect('datapoint_detail', datapoint_id=datapoint.id)
        
        scrape_datapoint_task.delay(datapoint.id)
        messages.success(request, f"Scraping initiated for Datapoint '{datapoint.name}'.")
        return redirect('datapoint_detail', datapoint_id=datapoint.id)

class ScrapeDataGroupView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View to trigger scraping for a specific DataGroup.
    """
    permission_required = 'datapointScraperApp.can_scrape_datagroup'  # Define appropriate permission

    def post(self, request, datagroup_id):
        datagroup = get_object_or_404(DataGroup, id=datagroup_id)
        # Optionally, check if any Datapoints are in 'AUTO' status
        auto_datapoints = datagroup.datapoints.filter(status=Datapoint.STATUS_AUTO)
        if not auto_datapoints.exists():
            messages.warning(request, f"No Datapoints in DataGroup '{datagroup.name}' are in 'AUTO' status.")
            return redirect('datagroup_detail', datagroup_id=datagroup.id)
        
        scrape_datagroup_task.delay(datagroup.id)
        messages.success(request, f"Scraping initiated for DataGroup '{datagroup.name}'.")
        return redirect('datagroup_detail', datagroup_id=datagroup.id)

class ScrapeOrganizationView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View to trigger scraping for a specific Organization.
    """
    permission_required = 'datapointScraperApp.can_scrape_organisation'  # Define appropriate permission

    def post(self, request, organisation_id):
        organisation = get_object_or_404(Organization, id=organisation_id)
        # Optionally, check if any Datapoints are in 'AUTO' status
        auto_datapoints = organisation.datapoints.filter(status=Datapoint.STATUS_AUTO)
        if not auto_datapoints.exists():
            messages.warning(request, f"No Datapoints in Organization '{organisation.name}' are in 'AUTO' status.")
            return redirect('organisation_detail', organisation_id=organisation.id)
        
        scrape_organisation_task.delay(organisation.id)
        messages.success(request, f"Scraping initiated for Organization '{organisation.name}'.")
        return redirect('organisation_detail', organisation_id=organisation.id)

class ScrapeAllDatapointsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View to trigger scraping for all Datapoints.
    """
    permission_required = 'datapointScraperApp.can_scrape_all_datapoints'  # Define appropriate permission

    def post(self, request):
        scrape_all_datapoints_task.delay()
        messages.success(request, "Scraping initiated for all Datapoints.")
        return redirect('home')  # Redirect to an appropriate page