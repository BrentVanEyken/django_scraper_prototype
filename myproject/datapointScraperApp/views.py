import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import models
from django.db.models import Count, Q
import requests
import os
import json

from .forms import RegisterForm, DatapointForm
from .models import Datapoint, Organization, DataGroup
from django.utils import timezone

from .tasks import (
    scrape_datapoint_task,
    scrape_datagroup_task,
    scrape_organisation_task,
    scrape_all_datapoints_task,
)

logger = logging.getLogger(__name__)

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


### VERSION WITH CELERY

# class ScrapeAllDatapointsView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """
#     View to trigger scraping for all Datapoints with status 'AUTO', 'VERIFY', or 'FIX'.
#     After scraping, updates the status based on the comparison between scraped data and current_verified_data.
#     """
#     permission_required = 'datapointScraperApp.can_scrape_all_datapoints'

#     def post(self, request):
#         # Get all Datapoint instances with status 'AUTO', 'VERIFY', or 'FIX'
#         datapoints = Datapoint.objects.filter(status__in=['AUTO', 'VERIFY', 'FIX'])
#         datapoint_ids = list(datapoints.values_list('id', flat=True))
        
#         if not datapoint_ids:
#             messages.warning(request, "No Datapoints in 'AUTO', 'VERIFY', or 'FIX' status to scrape.")
#             return redirect('home')  # Adjust as per your URL naming

#         # Prepare the scraping tasks with validation
#         tasks = []
#         for dp in datapoints:
#             if not dp.url or not dp.xpath:
#                 logger.warning(f"Datapoint '{dp.name}' is missing 'url' or 'xpath'. Skipping.")
#                 messages.warning(request, f"Datapoint '{dp.name}' is missing 'url' or 'xpath'. Skipping.")
#                 continue
#             if dp.data_type.upper() not in ['TXT', 'HTML']:
#                 logger.warning(f"Datapoint '{dp.name}' has invalid 'data_type': {dp.data_type}. Defaulting to 'TXT'.")
#                 data_type = 'TXT'
#             else:
#                 data_type = dp.data_type.upper()
            
#             tasks.append({
#                 "url": dp.url,
#                 "xpath": dp.xpath,
#                 "data_type": data_type
#             })

#         if not tasks:
#             messages.warning(request, "No valid Datapoints to scrape after validation.")
#             return redirect('home')

#         # Offload scraping to Celery
#         scrape_all_datapoints_task.delay(tasks)

#         messages.success(request, "Scraping initiated. You will receive a notification once it's complete.")
#         return redirect('home')




#### VERSION WITHOUT CELERY  

class ScrapeAllDatapointsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View to trigger scraping for all Datapoints with status 'AUTO', 'VERIFY', or 'FIX'.
    After scraping, updates the status based on the comparison between scraped data and current_verified_data.
    """
    permission_required = 'datapointScraperApp.can_scrape_all_datapoints'

    def post(self, request):
        # Get all Datapoint instances with status 'AUTO', 'VERIFY', or 'FIX'
        datapoints = Datapoint.objects.filter(status__in=['AUTO', 'VERIFY', 'FIX'])
        datapoint_ids = list(datapoints.values_list('id', flat=True))
        
        if not datapoint_ids:
            messages.warning(request, "No Datapoints in 'AUTO', 'VERIFY', or 'FIX' status to scrape.")
            return redirect('home')  # Adjust as per your URL naming

        # Prepare the scraping tasks with validation
        tasks = []
        for dp in datapoints:
            if not dp.url or not dp.xpath:
                logger.warning(f"Datapoint '{dp.name}' is missing 'url' or 'xpath'. Skipping.")
                messages.warning(request, f"Datapoint '{dp.name}' is missing 'url' or 'xpath'. Skipping.")
                continue
            if dp.data_type.upper() not in ['TXT', 'HTML']:
                logger.warning(f"Datapoint '{dp.name}' has invalid 'data_type': {dp.data_type}. Defaulting to 'TXT'.")
                data_type = 'TXT'
            else:
                data_type = dp.data_type.upper()
            
            tasks.append({
                "url": dp.url,
                "xpath": dp.xpath,
                "data_type": data_type
            })

        if not tasks:
            messages.warning(request, "No valid Datapoints to scrape after validation.")
            return redirect('home')

        payload = {
            "tasks": tasks
        }

        # Log the payload
        logger.debug(f"Scraping payload: {json.dumps(payload)}")

        # Retrieve the API token from Django settings
        API_TOKEN = settings.SCRAPER_API_TOKEN  # Ensure this is set in settings.py and loaded from .env

        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            # Send POST request to FastAPI scraper
            response = requests.post(
                "http://127.0.0.1:8001/scrape/batch",  # FastAPI batch endpoint on port 8001
                json=payload,
                headers=headers,
                timeout=60  # Increased timeout for batch processing
            )

            logger.info(f"FastAPI Response Status Code: {response.status_code}")
            logger.info(f"FastAPI Response Content: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                results = response_data.get("results", [])

                for result in results:
                    url = result.get("url")
                    xpath = result.get("xpath")
                    scraped_data = result.get("scraped_data")
                    status = result.get("status")
                    error = result.get("error")

                    try:
                        # Retrieve the corresponding Datapoint instance
                        dp = Datapoint.objects.get(url=url, xpath=xpath)

                        if status == "success":
                            # Compare scraped_data with current_verified_data
                            if dp.current_verified_data == scraped_data:
                                dp.status = "AUTO"
                                messages.success(request, f"No changes detected for Datapoint: {dp.name}. Status set to AUTO.")
                            else:
                                dp.status = "VERIFY"
                                messages.info(request, f"Changes detected for Datapoint: {dp.name}. Status set to VERIFY for user verification.")
                            
                            dp.current_unverified_data = scraped_data
                            dp.last_updated = timezone.now()
                            dp.save()
                        else:
                            dp.status = "FIX"
                            dp.last_updated = timezone.now()
                            dp.save()
                            messages.error(request, f"Failed to scrape Datapoint: {dp.name}. Error: {error}")
                    except Datapoint.DoesNotExist:
                        messages.error(request, f"Datapoint with URL {url} and XPath {xpath} does not exist.")

            else:
                # Attempt to extract error message from FastAPI response
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                except json.JSONDecodeError:
                    error_detail = response.text  # Capture raw response
                logger.error(f"FastAPI Error Response: {response.text}")
                messages.error(request, f"Failed to initiate scraping: {error_detail}")

        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException: {e}")
            messages.error(request, f"Error connecting to the scraper service: {e}")
        except json.JSONDecodeError:
            logger.error("JSONDecodeError: Invalid response from FastAPI.")
            messages.error(request, "Invalid response from the scraper service.")

        return redirect('home')  # Adjust as per your URL naming