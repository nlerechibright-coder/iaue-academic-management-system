# academics/urls.py
from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Sessions
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/edit/', views.session_edit, name='session_edit'), # <--- THIS WAS MISSING
    
    # Semesters
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/create/', views.semester_create, name='semester_create'),
]