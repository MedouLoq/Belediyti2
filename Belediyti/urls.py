# urls.py (Add the update API endpoint)
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views 
from Citoyen import views
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("superadmin/", include("super_admin.urls")), 
    path("muni_admin/", include("Muni_admin.urls")), 
    # Authentication
    path("register/", views.register, name="register"),
    path("redirect/", views.redirect_user, name="redirect_user"),
    path("login/", views.user_login, name="login"), 
    path("logout/", views.user_logout, name="logout"), 
    # Password Reset
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="citizens/password_reset.html"), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="citizens/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="citizens/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="citizens/password_reset_complete.html"), name="password_reset_complete"),

    # Dashboard
    path("dashboard/", views.citizen_dashboard, name="citizen_dashboard"),
    
    # Problems
    path("problems/report/", views.report_problem, name="report_problem"),
    path("problems/<uuid:pk>/", views.problem_detail, name="problem_detail"),
    path("problems/", views.problem_list, name="problem_list"),
    
    # Complaints
    path("complaints/submit/", views.submit_complaint, name="submit_complaint"),
    path("complaints/<uuid:pk>/", views.complaint_detail, name="complaint_detail"),
    path("complaints/", views.complaint_list, name="complaint_list"),
    path("get_municipality_id/", views.get_municipality_id, name="get_municipality_id"),
    
    # Profile (Web Views - keep if needed)
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # --- API Endpoints --- 
    path("api/login/", views.login_api, name="login_api"),
    path("api/register/", views.register_api, name="register_api"),
    # Profile API (GET)
    path("api/profile/", views.user_profile_api, name="user_profile_api"),
    # Profile Update API (GET, PUT, PATCH) - Add this line
    path("api/profile/update/", views.citizen_profile_update_api, name="citizen_profile_update_api"),
    # Municipalities API
    path("api/municipalities/", views.municipality_list_api, name="municipality_list_api"),
    # Dashboard API
    path("api/dashboard/stats/", views.dashboard_stats_api, name="dashboard_stats_api"),
    path("api/dashboard/activity/", views.recent_activity_api, name="recent_activity_api"),
    # Problems API
    path("api/problems/", views.problem_list_api, name="problem_list_api"),
    path("api/problems/", views.problem_list_api, name="problem_list_api"),
    path("api/problems/<uuid:pk>/", views.problem_detail_api, name="problem_detail_api"),
    path("api/problems/report/", views.report_problem_api, name="report_problem_api"),
    path("api/categories/", views.category_list_api, name="category_list_api"),
    # Notifications API
    path("api/notifications/", views.notification_list_api, name="notification_list_api"),
    path("api/notifications/<uuid:pk>/read/", views.mark_notification_read_api, name="mark_notification_read_api"),
    path("api/notifications/mark_all_read/", views.mark_all_notifications_read_api, name="mark_all_notifications_read_api"),
    # Verification API
    path("api/send-code/", views.SendVerificationCodeView.as_view(), name="send_code"),
    path("api/verify-code/", views.VerifyCodeView.as_view(), name="verify_code"),
path("api/complaints/", views.complaint_list_api, name="complaint_list_api"),
    path("api/complaints/<uuid:pk>/", views.complaint_detail_api, name="complaint_detail_api"),
    path("api/complaints/submit/", views.submit_complaint_api, name="submit_complaint_api"),

    # Def
    # Default path redirect
    path("", lambda request: redirect("login" if not request.user.is_authenticated else "redirect_user"), name="home_redirect"), 
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

