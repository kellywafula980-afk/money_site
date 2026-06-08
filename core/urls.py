from django.contrib import admin
from django.urls import path
# Import the exact view function we created
from jobs.views import job_list_view 

urlpatterns = [
    path('admin/', admin.site.urls),
    # Point your main root homepage directly to the clean job list view
    path('', job_list_view, name='homepage_job_board'), 
]