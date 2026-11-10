# staff/urls.py
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Staff Personal Dashboard
    path('dashboard/', views.staff_dashboard, name='dashboard'),
    
    # List all staff (Management only)
    path('', views.staff_list, name='list'),
    
    # Create new staff (Management only)
    path('create/', views.staff_create, name='staff_create'),
    
    # Edit existing staff
    path('<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    
    # Delete staff
    path('<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    
    # Manage Appointments (Roles)
    path('<int:pk>/appointments/', views.appointment_list, name='appointment_list'),
    path('<int:pk>/appointments/create/', views.appointment_create, name='appointment_create'),
]