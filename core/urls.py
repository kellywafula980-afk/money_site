from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from jobs.views import (
    debug_jobs, 
    generate_sitemap, 
    robots_txt,
    post_job_page,
    initiate_payment,
    payment_callback,
    paystack_webhook,  # <-- ADD THIS LINE

)

urlpatterns = [
    path('robots.txt', robots_txt, name='robots'),
    # core/urls.py
    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'), 
    path('admin/', admin.site.urls), 
    path('', include('jobs.urls')),
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    path('debug/', debug_jobs, name='debug'),
    path('post-job/', post_job_page, name='post_job'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('payment/callback/', payment_callback, name='payment_callback'),
    path('sitemap.xml', generate_sitemap, name='sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)