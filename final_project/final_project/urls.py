"""
URL configuration for final_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from trainings import views as t_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', t_views.MainView.as_view(), name='main'),
    path('employees/', t_views.EmployeesView.as_view(), name='employees_list'),
    path('employees/add/', t_views.AddEmployeeView.as_view(), name='add_employee'),
    path('employees/<int:pk>/edit/', t_views.EditEmployeeView.as_view(), name='edit_employee'),
    path('employees/<int:pk>/', t_views.EmployeeCoursesView.as_view(), name='employee_courses'),
    path('participants/add/', t_views.AddParticipantView.as_view(), name='add_participant'),
    path('courses/', t_views.CoursesView.as_view(), name='courses_list'),
    path('courses/add/', t_views.AddCourseView.as_view(), name='add_course'),
    path('courses/<int:pk>/', t_views.CourseDetailsView.as_view(), name='course_details'),
    path('courses/today/', t_views.CoursesForTodayView.as_view(), name='courses_today'),
    path('courses/<int:pk>/presence_list/', t_views.CoursePresenceListView.as_view(), name='course_presence_list'),
    path('courses/<int:pk>/participants/', t_views.CourseParticipantsView.as_view(), name='course_participants'),
    path('participants/edit/', t_views.EditParticipantView.as_view(), name='edit_participant'),
    path('participants/', t_views.ParticipantsView.as_view(), name='participants_list'),
    path('login/', t_views.LoginView.as_view(), name='login'),
    path('logout/', t_views.LogoutView.as_view(), name='logout'),
]
