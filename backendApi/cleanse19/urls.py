from django.urls import path, include

from cleanse19 import views

urlpatterns = [
    path('getPeopleCount/', views.getPeopleCount),
    path('getFaceMaskViolations/', views.getFaceMaskViolations),
    path('ipAddress/', views.IPAPIView.as_view()),
    path('', views.index, name="face_webcam_feed"),
    path('faceMaskDetection/', views.face_mask_detection, name='face_mask_detection') 
]