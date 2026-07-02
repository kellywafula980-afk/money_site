from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('post-job/', views.post_job, name='post_job'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
    path('save-job/<int:job_id>/', views.save_job, name='save_job'),
    path('profile/', views.profile, name='profile'),
    path('applications/', views.applications_view, name='applications'),
    path('review-application/<int:application_id>/', views.review_application, name='review_application'),
    path('toggle-job/<int:job_id>/', views.toggle_job_status, name='toggle_job'),
    path('api/stats/', views.dashboard_stats_api, name='stats_api'),
]
