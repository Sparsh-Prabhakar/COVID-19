from django.urls import include, path

from cleanse19 import views

urlpatterns = [
    path('getPeopleCount/', views.getPeopleCount),
    path('getFaceMaskViolations/', views.getFaceMaskViolations),
    path('ipAddress/', views.IPAPIView.as_view()),
    path('', views.index, name="index"),
    path('faceMaskDetection/', views.face_mask_detection, name='face_mask_detection'),
    path('crowdCounting/', views.crowd_counting),
    path('stopFaceMaskDetection/', views.stop_face_mask_detection),
    path('startRecordingFaceMask/', views.startRecordingFaceMask, name= 'start_recording_face_mask') ,
]
