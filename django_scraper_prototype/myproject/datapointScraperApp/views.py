from datetime import datetime
import logging
from django.forms import ValidationError
from django.core.validators import URLValidator
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

from .forms import RegisterForm, DatapointForm, TestXPathForm, UserSettingsForm
from .models import Datapoint, Organization, DataGroup
from django.utils import timezone

from .utils import perform_scraping, get_user_profile

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


@login_required
def user_settings(request):
    user_profile = get_user_profile(request.user)
    if request.method == 'POST':
        form = UserSettingsForm(request.POST)
        if form.is_valid():
            # Update Column Preferences
            selected_columns = form.cleaned_data['columns']
            user_profile.column_preferences = {col: True for col in selected_columns}
            # Set False for columns not selected
            all_columns = [choice[0] for choice in form.COLUMN_CHOICES]
            for col in all_columns:
                if col not in selected_columns:
                    user_profile.column_preferences[col] = False

            # Update Theme Preference
            user_profile.theme = form.cleaned_data['theme']

            user_profile.save()
            messages.success(request, "Your settings have been updated.")
            return redirect('user-settings')
    else:
        # Prepopulate the form with existing preferences
        existing_prefs = user_profile.column_preferences
        initial_columns = [col for col, visible in existing_prefs.items() if visible]
        form = UserSettingsForm(initial={
            'columns': initial_columns,
            'theme': user_profile.theme
        })
    return render(request, 'user_settings.html', {'form': form})


def datapoint_detail(request, pk):
    """
    Displays detailed information about a specific datapoint.
    """
    datapoint = get_object_or_404(Datapoint, pk=pk)
    return render(request, 'datapoint_detail.html', {'datapoint': datapoint})

def datapoint_edit(request, pk):
    """
    Allows editing of a specific datapoint.
    """
    datapoint = get_object_or_404(Datapoint, pk=pk)
    if request.method == 'POST':
        form = DatapointForm(request.POST, instance=datapoint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datapoint updated successfully.')
            return redirect('datapoint-list')
    else:
        form = DatapointForm(instance=datapoint)
    return render(request, 'datapoint_edit.html', {'form': form, 'datapoint': datapoint})

def datapoint_verify(request, pk):
    """
    Verifies a datapoint by updating its status to 'VERIFIED'.
    """
    datapoint = get_object_or_404(Datapoint, pk=pk)
    if request.method == 'POST':
        datapoint.status = 'AUTO'
        datapoint.last_verified = timezone.now()
        datapoint.save()
        messages.success(request, 'Datapoint verified successfully.')
        return redirect('datapoint-list')
    return render(request, 'datapoint_verify.html', {'datapoint': datapoint})

def datapoint_delete(request, pk):
    datapoint = get_object_or_404(Datapoint, pk=pk)
    if request.method == 'POST':
        datapoint.delete()
        return redirect('datapoint-list')
    return render(request, 'datapoint_confirm_delete.html', {'datapoint': datapoint})

def datapoint_revert(request, pk):
    datapoint = get_object_or_404(Datapoint, pk=pk)
    # Implement revert logic here
    return redirect('datapoint-list')

class DatapointCreateView(LoginRequiredMixin, CreateView):
    model = Datapoint
    form_class = DatapointForm
    template_name = 'datapoint_create.html' 
    success_url = reverse_lazy('datapoint-list')

    def get_initial(self):
        initial = super().get_initial()
        # Retrieve data from GET parameters
        url = self.request.GET.get('url', '').strip()
        xpath = self.request.GET.get('xpath', '').strip()
        scrape_result = self.request.GET.get('scrape_result', '').strip()
        data_type = self.request.GET.get('data_type', 'TXT').strip()
        # Basic validation for URL
        if url:
            validator = URLValidator()
            try:
                validator(url)
                initial['url'] = url
            except ValidationError:
                # Optionally, handle invalid URL
                pass
        if xpath:
            initial['xpath'] = xpath
        if scrape_result:
            initial['current_verified_data'] = scrape_result
        # Map 'data_type' from TestXPathForm to DatapointForm's 'data_type'
        # Ensure that the choices match or are correctly mapped
        # Assuming 'TXT' maps to 'STRING' and 'HTML' maps to 'HTML' (or another appropriate mapping)
        data_type_mapping = {
            'TXT': 'STRING',
            'HTML': 'HTML',
        }
        mapped_data_type = data_type_mapping.get(data_type.upper(), 'STRING')  # Default to 'STRING' if not found
        initial['data_type'] = mapped_data_type
        return initial

    def form_valid(self, form):
        """
        If the form is valid, save the associated model and trigger scraper if needed.
        """
        response = super().form_valid(form)  # This saves the form and sets self.object

        # # Check if the status is not set to 'AUTO'
        # if self.object.status != Datapoint.STATUS_AUTO:
        #     # Trigger the scraper logic synchronously
        #     try:
        #         perform_scraping(self.request, [self.object])
        #         messages.success(
        #             self.request, 
        #             f"Datapoint created with status '{self.object.get_status_display()}'. Scraping has been initiated."
        #         )
        #     except Exception as e:
        #         # Handle potential errors in triggering the scraping logic
        #         messages.error(
        #             self.request, 
        #             f"Datapoint created but failed to initiate scraping: {str(e)}"
        #         )
        #         # Optionally, you might want to handle the Datapoint instance accordingly

        # else:
        #     messages.success(self.request, 'Datapoint created successfully.')

        messages.success(self.request, 'Datapoint created successfully.')

        return response

class DatapointListView(ListView):
    model = Datapoint
    template_name = 'datapoint_list.html'
    context_object_name = 'datapoints'
    paginate_by = 20  # Adjust as needed
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization_id = self.request.GET.get('organization')
        status = self.request.GET.get('status')
        
        if organization_id:
            queryset = queryset.filter(organization__id=organization_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = Organization.objects.all()
        context['status_choices'] = Datapoint.STATUS_CHOICES
        # Preserve current filters in the context for template usage (e.g., in breadcrumbs)
        context['current_filters'] = {
            'organization': self.request.GET.get('organization', ''),
            'status': self.request.GET.get('status', ''),
        }

         # Determine which columns to show based on user preferences
        user_profile = self.request.user.profile
        column_prefs = user_profile.column_preferences

        # Default to showing all columns if no preferences are set
        default_columns = {
            '0': True,
            '1': True,
            '2': True,
            '3': True,
            '4': True,
            '5': True,
            '6': True,
            '7': True,
            '8': True,
            # '9': True,  # Actions column, always visible
        }

        # Merge default columns with user preferences
        columns_to_show = default_columns.copy()
        for col, visible in column_prefs.items():
            columns_to_show[col] = visible

        context['columns_to_show'] = columns_to_show
        return context

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
        
        if datapoint.status not in [Datapoint.STATUS_AUTO, Datapoint.STATUS_VERIFY, Datapoint.STATUS_FIX]:
            messages.warning(request, f"Datapoint '{datapoint.name}' is not in a scrappable status.")
            return redirect('datapoint_detail', pk=datapoint.id)
        
        try:
            perform_scraping(request, [datapoint])
            messages.success(request, f"Scraping initiated for Datapoint '{datapoint.name}'.")
        except Exception as e:
            messages.error(request, f"Failed to initiate scraping for Datapoint '{datapoint.name}': {str(e)}")

        return redirect('datapoint_detail', pk=datapoint.id)


# class ScrapeDataGroupView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """
#     View to trigger scraping for a specific DataGroup.
#     """
#     permission_required = 'datapointScraperApp.can_scrape_datagroup'  # Define appropriate permission

#     def post(self, request, datagroup_id):
#         datagroup = get_object_or_404(DataGroup, id=datagroup_id)
#         # Optionally, check if any Datapoints are in 'AUTO' status
#         auto_datapoints = datagroup.datapoints.filter(status=Datapoint.STATUS_AUTO)
#         if not auto_datapoints.exists():
#             messages.warning(request, f"No Datapoints in DataGroup '{datagroup.name}' are in 'AUTO' status.")
#             return redirect('datagroup_detail', datagroup_id=datagroup.id)
        
#         scrape_datagroup_task.delay(datagroup.id)
#         messages.success(request, f"Scraping initiated for DataGroup '{datagroup.name}'.")
#         return redirect('datagroup_detail', datagroup_id=datagroup.id)

# class ScrapeOrganizationView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """
#     View to trigger scraping for a specific Organization.
#     """
#     permission_required = 'datapointScraperApp.can_scrape_organisation'  # Define appropriate permission

#     def post(self, request, organisation_id):
#         organisation = get_object_or_404(Organization, id=organisation_id)
#         # Optionally, check if any Datapoints are in 'AUTO' status
#         auto_datapoints = organisation.datapoints.filter(status=Datapoint.STATUS_AUTO)
#         if not auto_datapoints.exists():
#             messages.warning(request, f"No Datapoints in Organization '{organisation.name}' are in 'AUTO' status.")
#             return redirect('organisation_detail', organisation_id=organisation.id)
        
#         scrape_organisation_task.delay(organisation.id)
#         messages.success(request, f"Scraping initiated for Organization '{organisation.name}'.")
#         return redirect('organisation_detail', organisation_id=organisation.id)

class ScrapeAllDatapointsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View to trigger scraping for all Datapoints with status 'AUTO', 'VERIFY', or 'FIX'.
    """
    permission_required = 'datapointScraperApp.can_scrape_all_datapoints'

    def post(self, request):
        # Get all Datapoint instances with status 'AUTO', 'VERIFY', or 'FIX'
        datapoints = Datapoint.objects.filter(status__in=[Datapoint.STATUS_AUTO, Datapoint.STATUS_VERIFY, Datapoint.STATUS_FIX])

        if not datapoints.exists():
            messages.warning(request, "No Datapoints in 'AUTO', 'VERIFY', or 'FIX' status to scrape.")
            return redirect('home')  # Adjust as per your URL naming

        # Trigger scraping for all relevant datapoints
        perform_scraping(request, datapoints)

        return redirect('home')

class TestXPathView(View):
    """
    View to allow users to test an XPath by providing a URL and XPath expression.
    """
    template_name = 'test_xpath.html'

    def get(self, request):
        """
        Handle GET requests: display the form.
        """
        form = TestXPathForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """
        Handle POST requests: process the form and display results.
        """
        form = TestXPathForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            xpath = form.cleaned_data['xpath']
            data_type = form.cleaned_data['data_type']

            # Prepare the scraping task
            task = {
                "tasks": [
                    {
                        "url": url,
                        "xpath": xpath,
                        "data_type": data_type
                    }
                ]
            }

            # Log the scraping task
            logger.debug(f"TestXPath Scraping task: {json.dumps(task)}")

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
                    json=task,
                    headers=headers,
                    timeout=60  # Adjust timeout as needed
                )

                logger.info(f"FastAPI Response Status Code: {response.status_code}")
                logger.info(f"FastAPI Response Content: {response.text}")

                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        logger.debug(f"Parsed JSON Response: {json.dumps(response_data)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSONDecodeError: {e}")
                        messages.error(request, "Received invalid JSON response from the scraper service.")
                        return render(request, self.template_name, {'form': form})

                    results = response_data.get("results", [])

                    if not results:
                        messages.warning(request, "No results returned from the scraper.")
                        return render(request, self.template_name, {'form': form})

                    result = results[0]  # Since we're testing a single task

                    if result.get("status") == "success":
                        scraped_data = result.get("scraped_data")
                        if scraped_data:
                            logger.info(f"Scraped Data: {scraped_data}")
                            return render(request, self.template_name, {
                                'form': form,
                                'scraped_data': scraped_data,
                                'data_type': data_type,  # Ensure this is included
                                'success': True
                            })
                        else:
                            logger.warning("Scraped data is empty.")
                            messages.warning(request, "Scraping succeeded but no data was found with the provided XPath.")
                            return render(request, self.template_name, {'form': form})
                    else:
                        error = result.get("error", "Unknown error occurred during scraping.")
                        logger.error(f"Scraping failed: {error}")
                        messages.error(request, f"Scraping failed: {error}")
                        return render(request, self.template_name, {'form': form})
                else:
                    # Attempt to extract error message from FastAPI response
                    try:
                        error_detail = response.json().get("detail", "Unknown error")
                    except json.JSONDecodeError:
                        error_detail = response.text  # Capture raw response
                    logger.error(f"FastAPI Error Response: {response.text}")
                    messages.error(request, f"Failed to initiate scraping: {error_detail}")
                    return render(request, self.template_name, {'form': form})

            except requests.exceptions.RequestException as e:
                logger.error(f"RequestException: {e}")
                messages.error(request, f"Error connecting to the scraper service: {e}")
                return render(request, self.template_name, {'form': form})
            except json.JSONDecodeError:
                logger.error("JSONDecodeError: Invalid response from FastAPI.")
                messages.error(request, "Invalid response from the scraper service.")
                return render(request, self.template_name, {'form': form})
        else:
            # Form is invalid
            messages.error(request, "Please correct the errors below.")
            return render(request, self.template_name, {'form': form})
