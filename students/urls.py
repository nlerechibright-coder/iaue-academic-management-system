# students/urls.py
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student dashboard
    path('dashboard/', views.student_dashboard, name='dashboard'),

    # List all students
    path('', views.student_list, name='list'),

    # Register/Create new student (Replaces 'clearance' concept)
    path('create/', views.student_create, name='student_create'),

    # Edit existing student
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),

    # Delete student
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),

    # View specific student profile/details
    path('<int:pk>/', views.student_detail, name='student_detail'),
]