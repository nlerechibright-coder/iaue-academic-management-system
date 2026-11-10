from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('create/', views.staff_create, name='staff_create'),
    path('list/', views.staff_list, name='staff_list'),
]
