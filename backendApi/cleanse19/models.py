from django.contrib.auth.models import User as authUser
from django.db import models


# Create your models here.
class IP_address(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE, default=None)
    name = models.CharField(max_length=255, default=None, null=True)
    ip_address = models.CharField(max_length=255, default=None, null=True)

class Face_mask(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE, default=None)
    violations = models.IntegerField()
    timestamp =  models.DateTimeField(auto_now_add=True)
    last_mail_time = models.DateTimeField(auto_now_add= True) 
    
class Crowd_counting(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE, default=None)
    people_count = models.IntegerField()
    timestamp =  models.DateTimeField(auto_now_add=True)
    max_count = models.IntegerField(default= 0)
    last_mail_time = models.DateTimeField(auto_now_add= True) 

class Social_distancing(models.Model):
    user = models.ForeignKey(authUser, on_delete=models.CASCADE)
    violations = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add= True)
    last_mail_time = models.DateTimeField(auto_now_add= True) 

class Recording(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE)
    name = models.CharField(max_length=100)
    is_recording = models.BooleanField(default=False)

class FaceMaskAnalysis(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE)
    violations = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add= True)

class SocialDistancingAnalysis(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE)
    violations = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add= True)

class CrowdCountingAnalysis(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE)
    count = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add= True)