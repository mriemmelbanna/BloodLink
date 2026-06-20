from django.urls import path
from . import views
from .views_reports import admin_reports

urlpatterns = [
    # تسجيل الدخول والخروج
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # تسجيل المستخدمين
    path('register/', views.register_choice, name='register_choice'),
    path('register/donor/', views.donor_register, name='donor_register'),
    path('register/patient/', views.patient_register, name='patient_register'),
    path('register/hospital/', views.hospital_register, name='hospital_register'),

    # dashboards لكل نوع
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
   

    # to generate reports for admin
    path('admin-reports/', admin_reports, name='admin_reports'),
    path("hospital/<int:hospital_id>/request/", views.request_hospital, name="request_hospital"),
   
]

