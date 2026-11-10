# courses/urls.py
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course Catalogue Management
    path('', views.course_list, name='list'),
    path('create/', views.course_create, name='course_create'),
    path('<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # New: Offering & Assignment Management
    path('offerings/', views.offering_list, name='offering_list'),
    path('offerings/generate/', views.generate_offerings, name='generate_offerings'), # NEW ROUTE
    path('offerings/<int:pk>/assignments/', views.manage_assignments, name='manage_assignments'),
]