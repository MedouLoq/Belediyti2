"""
URL configuration for Belediyti project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views 
from Citoyen import views
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication
    path('register/', views.register, name='register'),
    # Use your custom login view
    path('login/', views.user_login, name='login'), 
    # Use your custom logout view
    path('logout/', views.user_logout, name='logout'), 
    # Optional: Password Reset URLs (use Django's built-in)
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='citizens/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='citizens/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='citizens/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='citizens/password_reset_complete.html'), name='password_reset_complete'),

    # Dashboard
    path('dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    
    # Problems
    path('problems/report/', views.report_problem, name='report_problem'),
    path('problems/<uuid:pk>/', views.problem_detail, name='problem_detail'),
    path('problems/', views.problem_list, name='problem_list'),
    
    # Complaints
    path('complaints/submit/', views.submit_complaint, name='submit_complaint'),
    path('complaints/<uuid:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaints/', views.complaint_list, name='complaint_list'),
     path('get_municipality_id/', views.get_municipality_id, name='get_municipality_id'),
    # Profile
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Optional: Default path could redirect to login or dashboard
    path('', lambda request: redirect('login' if not request.user.is_authenticated else 'citizen_dashboard'), name='home_redirect'), 
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)