from django.db import models

# Create your models here.
class IP_address(models.Model):
    user_id = models.CharField(max_length=255)
    face_mask_ip = models.CharField(max_length=255)
    crowd_ip = models.CharField(max_length=255)

class Face_mask(models.Model):
    user_id = models.CharField(max_length=255)
    violations = models.IntegerField()
    timestamp =  models.DateTimeField(auto_now_add=True)

class Crowd_counting(models.Model):
    user_id = models.CharField(max_length=255)
    people_count = models.IntegerField()
    timestamp =  models.DateTimeField(auto_now_add=True)
