from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.http.response import StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .camera import *
from .models import *
from .serializers import *

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
    record = Recording.objects.filter(user= 1).filter(name='face_mask')
    return render(request, 'index.html', {'record': record[0]})

def gen(camera, request):
    while True:
        frame = camera.get_frame(request)
        yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def destroy(camera):
    camera.delete()

@csrf_exempt                
def face_mask_detection(request):
    return StreamingHttpResponse(gen(FaceMaskDetection(), request), content_type='multipart/x-mixed-replace; boundary=frame')
    

@csrf_exempt
def stop_face_mask_detection(request):
    record = Recording.objects.filter(name= 'face_mask').update(is_recording= False)
    destroy(FaceMaskDetection())
    return redirect('/')

def crowd_counting(request):
    return StreamingHttpResponse(gen(CrowdCounting(), request), content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def startRecordingFaceMask(request):
    Recording.objects.filter(name= 'face_mask').update(is_recording= True)
    return redirect('/')
