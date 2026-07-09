from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list_view, name='home'),
    path('jobs/<slug:slug>/', views.job_detail_view, name='detail'),
    path('jobs/<int:job_id>/', views.legacy_job_detail, name='job_detail_legacy'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/<path:company_name>/', views.company_detail, name='company_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<str:category_name>/', views.category_detail, name='category_detail'),
    path('run-production-sync/', views.secret_trigger_scraper, name='run_scraper'),
    path('download/<path:file_path>/', views.serve_media_file, name='download_file'),
]
