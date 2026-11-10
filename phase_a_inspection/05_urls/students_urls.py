from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('clearance/', views.student_clearance, name='student_clearance'),
    path('list/', views.student_list, name='student_list'),
]
