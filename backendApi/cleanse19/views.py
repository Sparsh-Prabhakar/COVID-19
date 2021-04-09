from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.http.response import StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import *
from .serializers import *

from .camera import *

# Create your views here.

@csrf_exempt
@require_http_methods(["POST"])
def getPeopleCount(request):
    if request.method == 'POST':
        # id = request.user_id
        count = serializers.serialize('json', Crowd_counting.objects.filter(user_id="1"))
        return JsonResponse(count, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def getFaceMaskViolations(request):
    if request.method == 'POST':
        # id = request.user_id
        violations = serializers.serialize('json', Face_mask.objects.filter(user_id="1"))
        return JsonResponse(violations, safe=False)

class IPAPIView(APIView):

    def get_objects(self, request):
        try:
            return IP_address.objects.get(user= request.user.id)
        except:
            return HttpResponse(status= status.HTTP_404_NOT_FOUND)

    def get(self, request):
        ip = self.get_objects(request)
        serializer = IPSerializer(ip)
        return Response(serializer.data)

    def post(self, request):
        serializer = IPSerializer(data= request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        ip = self.get_objects(request)
        serializer = IPSerializer(ip, data= request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def index(request):
    return render(request, 'index.html')

def gen(camera, request):
    while True:
        frame = camera.get_frame(request)
        yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                
def face_mask_detection(request):
        return StreamingHttpResponse(gen(FaceMaskDetection(), request), content_type='multipart/x-mixed-replace; boundary=frame')