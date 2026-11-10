# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from institution.views import management_dashboard
from accounts.views import user_login, user_logout
from results.views import dean_dashboard, exams_dashboard, hod_dashboard, result_dashboard

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # Authentication
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    # Root Dashboard (Management)
    # Maps '/' to the management dashboard view
    path('', management_dashboard, name='dashboard'),
    
    # App Modules with Namespaces
    # Institution: Faculties, Departments, Programmes
    # Assumes institution/urls.py has app_name='institution'
    path('management/institution/', include('institution.urls', namespace='institution')),
    
    # Staff: Staff profiles, appointments
    # Assumes staff/urls.py has app_name='staff'
    path('management/staff/', include('staff.urls', namespace='staff')),
    
    # Students: Registration, profiles
    # Assumes students/urls.py has app_name='students'
    # Keeping /student/ as per previous testing patterns
    path('student/', include('students.urls', namespace='students')),
    
    # Courses: Course catalog, offerings
    # Assumes courses/urls.py has app_name='courses'
    path('management/courses/', include('courses.urls', namespace='courses')),
    
    # Academics: Sessions, Semesters
    # Assumes academics/urls.py has app_name='academics'
    path('management/academics/', include('academics.urls', namespace='academics')),

    # Student registration workflow
    path('student/registration/', include('registration.urls', namespace='registration')),

    # Result processing workflow
    path('results/', include('results.urls', namespace='results')),
    path('management/results/', result_dashboard, name='management_results_dashboard'),
    path('management/hod/', hod_dashboard, name='hod_dashboard'),
    path('management/dean/', dean_dashboard, name='dean_dashboard'),
    path('management/exams-records/', exams_dashboard, name='exams_records_dashboard'),

    # Audit trail
    path('management/audit/', include('audit.urls', namespace='audit')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)