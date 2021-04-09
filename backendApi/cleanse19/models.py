from django.db import models
from django.contrib.auth.models import User as authUser

# Create your models here.
class IP_address(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE, default=None)
    face_mask_ip = models.CharField(max_length=255, default=None, null=True)
    crowd_ip = models.CharField(max_length=255, default=None, null=True)

class Face_mask(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE, default=None)
    violations = models.IntegerField()
    timestamp =  models.DateTimeField(auto_now_add=True)

class Crowd_counting(models.Model):
    user = models.ForeignKey(authUser, on_delete= models.CASCADE, default=None)
    people_count = models.IntegerField()
    timestamp =  models.DateTimeField(auto_now_add=True)
