from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('evaluate/', views.evaluate, name='evaluate'),
    path('portal/', views.student_portal, name='student_portal'),
    path('submit/<int:question_id>/', views.submit_answer, name='submit_answer'),
    path('result/<int:submission_id>/', views.result_view, name='result_view'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
]