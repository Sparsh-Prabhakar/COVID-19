from django.urls import include, path

from cleanse19 import views

urlpatterns = [
    path('', views.landing, name= 'landing'),
    path('home/', views.home, name='home'),
    path('faceMaskDetectionView/', views.faceMaskDetectionView, name='face_mask_detection_view'),
    path('faceMaskDetection/', views.face_mask_detection, name='face_mask_detection'),
    path('crowdCounting/', views.crowd_counting, name= 'crowd_counting'),
    path('stopRecordingFaceMaskDetection/', views.stopRecordingFaceMask, name='stop_recording_face_mask'),
    path('startRecordingFaceMask/', views.startRecordingFaceMask, name= 'start_recording_face_mask'),
    path('startRecordingCrowdCounting/', views.startRecordingCrowdCounting,name= 'start_recording_crowd_counting'),
    path('stopRecordingCrowdCounting/', views.stopRecordingCrowdCounting, name= 'stop_recording_crowd_counting'),
    path('crowdCountingView/', views.crowdCountingView, name= 'crowd_counting_view'),
    path('socialDistancingView/', views.socialDistancingView, name= 'social_distancing_view'),
    path('socialDistancing', views.social_distancing, name= 'social_distancing'),
    path('startRecordingSocialDistancing', views.startRecordingSocialDistancing, name='start_recording_social_distancing'),
    path('stopRecordingSocialDistancing', views.stopRecordingSocialDistancing, name='stop_recording_social_distancing'),
    path('profile',views.profile,name="profile"),
    path('profile_save/',views.profile_save, name="profile_save"),
    path('help',views.help,name="help"),
    path('send_email/',views.send_email, name="send_email"),
    path('analysis',views.analysis,name="analysis"),
    path('getFaceMaskViolationsCount', views.getFaceMaskViolationsCount, name='get_face_mask_violations_count'),
    path('getPeopleCount', views.getPeopleCount, name= 'get_people_count'),
    path('getSocialDistancingViolationsCount', views.getSocialDistancingViolationsCount, name='get_social_distancing_violations_count')    
]