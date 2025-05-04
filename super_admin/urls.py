# super_admin/urls.py
from django.urls import path
from . import views  # Import views from the current directory
app_name = 'superadmin'
urlpatterns = [
    # Define your superadmin URL patterns here
    path('', views.superadmin_home, name='superadmin_home'), # Example
    path('municipality_list/', views.municipality_list, name='municipality_list'),
    path('municipality/create/', views.municipality_create, name='municipality_create'),
    path('<int:pk>/update/', views.municipality_update, name='municipality_update'),
    path('<int:pk>/delete/', views.municipality_delete, name='municipality_delete'),
    path('<int:pk>/detail/', views.municipality_detail, name='municipality_detail'),
path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/update/<int:pk>/', views.update_category, name='update_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
     # Detail view (to get category info for pre-filling the form):
    path('categories/detail/<int:pk>/', views.category_detail, name='category_detail'), #add this url
     path('admins/', views.admin_user_list, name='admin_users'),
    path('admins/create/', views.create_admin_user, name='create_admin_user'),
    path('admins/update/<int:pk>/', views.update_admin_user, name='update_admin_user'),
    path('admins/delete/<int:pk>/', views.delete_admin_user, name='delete_admin_user'),

    # Citizen User Management
    path('citizens/', views.citizen_user_list, name='citizen_users'), 
]