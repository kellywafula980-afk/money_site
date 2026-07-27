from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # ============================================================
    # HOMEPAGE & JOB LISTINGS
    # ============================================================
    path('', views.job_list_view, name='home'),
    
    # ============================================================
    # JOB DETAILS
    # ============================================================
    path('jobs/<slug:slug>/', views.job_detail_view, name='detail'),
    path('jobs/<int:job_id>/', views.legacy_job_detail, name='job_detail_legacy'),
    
    # ============================================================
    # COMPANY PAGES
    # ============================================================
    path('companies/', views.company_list, name='company_list'),
    path('companies/<path:company_name>/', views.company_detail, name='company_detail'),
    
    # ============================================================
    # CATEGORY PAGES
    # ============================================================
    path('categories/', views.category_list, name='category_list'),
    path('categories/<str:category_name>/', views.category_detail, name='category_detail'),
    
    # ============================================================
    # JOB POSTING & PAYMENT
    # ============================================================
    path('post-job/', views.post_job_page, name='post_job'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('initiate-subscription/', views.initiate_subscription, name='initiate_subscription'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('webhook/', views.paystack_webhook, name='paystack_webhook'),  # ✅ Webhook endpoint
    
    # ============================================================
    # SITEMAP
    # ============================================================
    path('sitemap.xml/', views.generate_sitemap, name='sitemap'),
    
    # ============================================================
    # ROBOTS.TXT
    # ============================================================
    path('robots.txt/', views.robots_txt, name='robots_txt'),
    
    # ============================================================
    # INTERNAL UTILITIES (with secret keys)
    # ============================================================
    path('run-production-sync/', views.secret_trigger_scraper, name='run_scraper'),
    path('enrich-jobs/', views.enrich_jobs_endpoint, name='enrich_jobs'),
    path('debug-jobs/', views.debug_jobs, name='debug_jobs'),
    path('category-debug/', views.category_debug, name='category_debug'),
    path('run-migrations/', views.run_migrations, name='run_migrations'),
    path('create-categories/', views.create_categories_production, name='create_categories'),
    path('categorize-jobs/', views.categorize_jobs_production, name='categorize_jobs'),
    path('force-categorize/', views.force_assign_categories, name='force_categorize'),
    path('simple-categorize/', views.simple_categorize, name='simple_categorize'),
    
    # ============================================================
    # MEDIA FILE SERVING
    # ============================================================
    path('download/<path:file_path>/', views.serve_media_file, name='download_file'),
    path('create-superuser/', views.create_superuser, name='create_superuser'),
]