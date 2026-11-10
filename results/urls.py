from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    # Main Result Dashboard (Staff/Admin View)
    path('', views.result_dashboard, name='dashboard'),
    
    # Student Results View
    path('student/', views.student_view_results, name='student_results'),
    
    # Initialize/Create Sheet for an Offering
    path('init/<int:offering_id>/', views.init_result_sheet, name='init_sheet'),

    # Specific Sheet Detail
    path('<int:pk>/', views.result_sheet_detail, name='sheet_detail'),
    
    # Manual Save Endpoint (For Online Editing without CSV)
    path('<int:pk>/save-manual/', views.save_manual_scores, name='save_manual_scores'),
    
    # Approval Actions
    path('<int:pk>/approve-hod/', views.hod_approve_result_sheet, name='hod_approve'),
    path('<int:pk>/return-hod/', views.hod_return_result_sheet, name='hod_return'), # NEW
    
    path('<int:pk>/approve-dean/', views.dean_approve_result_sheet, name='dean_approve'),
    path('<int:pk>/return-dean/', views.dean_return_result_sheet, name='dean_return'), # NEW
    
    path('<int:pk>/verify-er/', views.exams_verify_result_sheet, name='er_verify'),
    path('<int:pk>/publish/', views.publish_result_sheet, name='publish'),
    path('<int:pk>/return-er/', views.er_return_result_sheet, name='er_return'), # NEW
    
    path('<int:pk>/submit/', views.submit_result_sheet, name='submit'),
    
    # Upload CSV for a specific sheet
    path('<int:pk>/upload-csv/', views.upload_result_csv, name='upload_csv'),
    
    # Download Template for a specific course/sheet
    path('template/<int:pk>/', views.download_result_template, name='download_template'),
    
    # Download Generic Blank Template (No PK required)
    path('template/generic/', views.download_result_template, name='download_generic_template'),
    
    # Role-Specific Dashboards
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('dean/', views.dean_dashboard, name='dean_dashboard'),
    path('exams/', views.exams_dashboard, name='exams_dashboard'),
]
