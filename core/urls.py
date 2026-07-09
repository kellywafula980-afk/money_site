from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from jobs import views as jobs_views
from dashboard import views as dashboard_views

urlpatterns = [
    # ============================================================
    # CORE ROUTES
    # ============================================================
    path('robots.txt', jobs_views.robots_txt, name='robots'),
    path('admin/', admin.site.urls),
    
    # ============================================================
    # JOB ROUTES (includes new slug-based URLs)
    # ============================================================
    path('', include('jobs.urls')),  # All job routes are now in jobs/urls.py
    
    # ============================================================
    # 🔐 AUTHENTICATION
    # ============================================================
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', dashboard_views.signup, name='signup'),
    
    # ============================================================
    # 📊 DASHBOARD
    # ============================================================
    path('dashboard/', include('dashboard.urls')),
    
    # ============================================================
    # VERIFICATION FILES
    # ============================================================
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    
    # ============================================================
    # DEBUG ENDPOINTS
    # ============================================================
    path('debug/', jobs_views.debug_jobs, name='debug'),
    path('category-debug/', jobs_views.category_debug, name='category_debug'),
    
    # ============================================================
    # JOB POSTING & PAYMENTS
    # ============================================================
    path('post-job/', jobs_views.post_job_page, name='post_job'),
    path('initiate-payment/', jobs_views.initiate_payment, name='initiate_payment'),
    path('payment/callback/', jobs_views.payment_callback, name='payment_callback'),
    
    # ============================================================
    # SITEMAP
    # ============================================================
    path('sitemap.xml', jobs_views.generate_sitemap, name='sitemap'),
    
    # ============================================================
    # 🚀 SCRAPER & ENRICHMENT ENDPOINTS
    # ============================================================
    path('scraper/trigger/', jobs_views.secret_trigger_scraper, name='trigger_scraper'),
    path('enrich-jobs/', jobs_views.enrich_jobs_endpoint, name='enrich_jobs'),
    
    # ============================================================
    # MIGRATIONS & UTILITY
    # ============================================================
    path('migrate/', jobs_views.run_migrations, name='run_migrations'),
    
    # ============================================================
    # CATEGORY MANAGEMENT
    # ============================================================
    path('create-categories-prod/', jobs_views.create_categories_production, name='create_categories_prod'),
    path('categorize-jobs-prod/', jobs_views.categorize_jobs_production, name='categorize_jobs_prod'),
    path('force-assign-categories/', jobs_views.force_assign_categories, name='force_assign_categories'),
    path('simple-categorize/', jobs_views.simple_categorize, name='simple_categorize'),
]

# ✅ Serve media files in development - THIS MUST BE AT THE END
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)