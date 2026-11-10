# registration/urls.py
from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    # Main Dashboard: Lists available courses filtered by dept/level
    path('', views.registration_dashboard, name='dashboard'),
    
    # Action: Add a specific Course Offering to the student's schedule
    path('add/<int:offering_id>/', views.register_course, name='register_course'),
    
    # Action: Remove/Withdraw a specific Course Offering from the schedule
    path('remove/<int:offering_id>/', views.unregister_course, name='unregister_course'),
    
    # Action: Finalize Registration (Change status from DRAFT to PENDING)
    path('confirm/', views.confirm_registration, name='confirm_registration'),
]