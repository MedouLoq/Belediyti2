# super_admin/urls.py
from django.urls import path
from . import views  # Import views from the current directory
app_name = 'Muni_admin'
urlpatterns = [
    # Define your superadmin URL patterns here
    path('', views.dashboard, name='admin_home'), # Example
    path('problems/', views.problem_list, name='problems'), #main
    path('dashboard/', views.dashboard, name='dashboard'),
    path('problems/<uuid:problem_id>/detail/', views.problem_detail, name='problem_detail'),
    
    # Complaint URLs
    path('complaints/', views.complaint_list, name='complaints'),
    path('complaints/<uuid:complaint_id>/detail/', views.complaint_detail, name='complaint_detail'),
    
    # Citizen URLs
    path('citizens/', views.citizen_list, name='citizens'),
    path('citizens/<int:citizen_id>/detail/', views.citizen_detail, name='citizen_detail'),
    
    # Media viewer
    path('media/<str:media_type>/<uuid:media_id>/', views.media_viewer, name='media_viewer'),
    
    # Bulk actions
    path('bulk-actions/', views.bulk_actions, name='bulk_actions'),
    
    # Report URLs 
    path('reports/', views.report_dashboard, name='report_dashboard'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    # --- ADD THESE NEW URLS FOR THE CHATBOT ---
        path('chatbot/', views.chatbot_page, name='chatbot_page'),
    path('api/chatbot/', views.ChatbotAPIView.as_view(), name='chatbot_api'),

]

