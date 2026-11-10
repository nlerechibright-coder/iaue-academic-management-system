from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Offerings
    path('offerings/', views.offering_list, name='offering_list'),
    path('offerings/create/', views.offering_create, name='offering_create'),
    path('offerings/<int:pk>/edit/', views.offering_edit, name='offering_edit'),
    path('offerings/<int:pk>/delete/', views.offering_delete, name='offering_delete'),
    
    # Sections
    path('sections/', views.section_list, name='section_list'),
    path('sections/create/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_edit, name='section_edit'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),
    
    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
]
