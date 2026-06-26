from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from jobs import views

urlpatterns = [
    # ============================================================
    # CORE ROUTES
    # ============================================================
    path('robots.txt', views.robots_txt, name='robots'),
    path('admin/', admin.site.urls),
    path('', include('jobs.urls')),
    
    # ============================================================
    # VERIFICATION FILES
    # ============================================================
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    
    # ============================================================
    # DEBUG ENDPOINTS
    # ============================================================
    path('debug/', views.debug_jobs, name='debug'),
    path('category-debug/', views.category_debug, name='category_debug'),
    
    # ============================================================
    # JOB POSTING & PAYMENTS
    # ============================================================
    path('post-job/', views.post_job_page, name='post_job'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    
    # ============================================================
    # SITEMAP
    # ============================================================
    path('sitemap.xml', views.generate_sitemap, name='sitemap'),
    
    # ============================================================
    # 🚀 SCRAPER & ENRICHMENT ENDPOINTS (ADD THESE)
    # ============================================================
    path('scraper/trigger/', views.secret_trigger_scraper, name='trigger_scraper'),
    path('enrich-jobs/', views.enrich_jobs_endpoint, name='enrich_jobs'),
    
    # ============================================================
    # MIGRATIONS & UTILITY
    # ============================================================
    path('migrate/', views.run_migrations, name='run_migrations'),
    
    # ============================================================
    # CATEGORY MANAGEMENT
    # ============================================================
    path('create-categories-prod/', views.create_categories_production, name='create_categories_prod'),
    path('categorize-jobs-prod/', views.categorize_jobs_production, name='categorize_jobs_prod'),
    path('force-assign-categories/', views.force_assign_categories, name='force_assign_categories'),
    path('simple-categorize/', views.simple_categorize, name='simple_categorize'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)