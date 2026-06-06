# jobs/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('post-a-job/', views.post_job, name='post_job'), # New layout
]