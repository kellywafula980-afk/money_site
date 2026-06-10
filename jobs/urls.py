from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list_view, name='home'),
    path('run-production-sync/', views.secret_trigger_scraper, name='trigger_scraper'),
    path('jobs/<int:job_id>/', views.job_detail_view, name='job_detail'),  # ADD THIS LINE

]