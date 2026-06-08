from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # 🔧 Fixed this line right here (removed the duplicate admin_site prefix)
    path('admin/', admin.site.urls), 
    
    path('', include('jobs.urls')),
    
    # This maps perfectly to jobs/templates/jobs/ads.txt
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
]
