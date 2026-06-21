from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from jobs import views

urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots'),
    path('admin/', admin.site.urls),
    path('', include('jobs.urls')),
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    path('debug/', views.debug_jobs, name='debug'),
    path('category-debug/', views.category_debug, name='category_debug'),
    path('post-job/', views.post_job_page, name='post_job'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('sitemap.xml', views.generate_sitemap, name='sitemap'),
    path('migrate/', views.run_migrations, name='run_migrations'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
