# super_admin/urls.py
from django.urls import path
from . import views  # Import views from the current directory
app_name = 'Muni_admin'
urlpatterns = [
    # Define your superadmin URL patterns here
    path('', views.dashboard, name='admin_home'), # Example
    path('problems/', views.problem_list, name='problems'), #main
     path('dashboard/', views.dashboard, name='dashboard'),
      path('problems/<uuid:problem_id>/detail/', views.problem_detail, name='problem_detail')

]