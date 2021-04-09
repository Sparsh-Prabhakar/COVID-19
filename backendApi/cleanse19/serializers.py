from rest_framework import serializers
from .models import *

class IPSerializer(serializers.ModelSerializer):
   class Meta:
       model = IP_address
       fields = '__all__'