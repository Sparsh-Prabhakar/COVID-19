from django.urls import path, include

from cleanse19 import views

urlpatterns = [
    path('getPeopleCount/', views.getPeopleCount),
    path('getFaceMaskViolations/', views.getFaceMaskViolations)
]