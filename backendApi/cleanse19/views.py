from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
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
@login_required(login_url = '/')
@require_http_methods(["POST"])
def getPeopleCount(request):
    if request.method == 'POST':
        # id = request.user_id
        count = serializers.serialize('json', Crowd_counting.objects.filter(user_id="1"))
        return JsonResponse(count, safe=False)

@csrf_exempt
@login_required(login_url = '/')
@require_http_methods(["POST"])
def getFaceMaskViolations(request):
    if request.method == 'POST':
        # id = request.user_id
        violations = serializers.serialize('json', Face_mask.objects.filter(user_id="1"))
        return JsonResponse(violations, safe=False)

@login_required(login_url = '/')
def user_data(request):
    user = dict()
    if Recording.objects.filter(user= request.user.id, name='face_mask').exists():
        face = Recording.objects.filter(user= request.user.id, name='face_mask')
        user.update({ 'face': face })
    if Recording.objects.filter(user= request.user.id, name='crowd_counting').exists():
        crowd = Recording.objects.filter(user= request.user.id, name='crowd_counting')
        user.update({ 'crowd': crowd })
    if Recording.objects.filter(user= request.user.id, name='social_distancing').exists():
        social = Recording.objects.filter(user= request.user.id, name='social_distancing')
        user.update({'social': social })
    if IP_address.objects.filter(user= request.user.id, name='face_mask').exists():
        face_ip = IP_address.objects.filter(user= request.user.id, name='face_mask')
        user.update({ 'face_ip': face_ip })
    if IP_address.objects.filter(user= request.user.id, name='crowd_counting').exists():
        crowd_ip = IP_address.objects.filter(user= request.user.id, name='crowd_counting')
        user.update({ 'crowd_ip': crowd_ip })
    if IP_address.objects.filter(user= request.user.id, name='social_distancing').exists():
        social_ip = IP_address.objects.filter(user= request.user.id, name='social_distancing')
        user.update({'social_ip': social_ip })

    print(face_ip[0])
    return user

@login_required(login_url = '/')
def home(request):
    user = user_data(request)
    return render(request, 'home.html', user)

# @login_required(login_url = '/')/
def gen(camera, request):
    while True:
        frame = camera.get_frame(request)
        yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# @login_required(login_url = '/')
def destroy(camera):
    camera.delete()

@login_required(login_url = '/')
def faceMaskDetectionView(request):
    user = user_data(request)
    return render(request, 'face.html', user)

@login_required(login_url = '/')
@csrf_exempt                
def face_mask_detection(request):
    return StreamingHttpResponse(gen(FaceMaskDetection(request), request), content_type='multipart/x-mixed-replace; boundary=frame')
    
# @login_required(login_url = '/')
@csrf_exempt
def stopRecordingFaceMask(request):
    record = Recording.objects.filter(name= 'face_mask').update(is_recording= False)
    destroy(FaceMaskDetection(request))
    return redirect('/faceMaskDetectionView/')

@login_required(login_url = '/')
def startRecordingFaceMask(request):
    if request.method == 'POST':
        if Recording.objects.filter(user= request.user.id, name= 'face_mask').exists():
            Recording.objects.filter(name= 'face_mask').update(is_recording= True)
        else:
            record = Recording.objects.create(
                name= 'face_mask',
                is_recording= True,
                user= authUser.objects.get(id= request.user.id)
            ).save()

        if request.POST['ipaddress'] != '':
            ip = request.POST['ipaddress']

        if IP_address.objects.filter(user= request.user.id, name= 'face_mask').exists():
            IP_address.objects.filter(user= request.user.id, name= 'face_mask').update(ip_address= ip)
        else:
            IP_address.objects.create(
                user= authUser.objects.get(id= request.user.id),
                name= 'face_mask',
                ip_address= ip
            ).save()
        return redirect('/faceMaskDetectionView/')

@login_required(login_url = '/')
def crowd_counting(request):
    return StreamingHttpResponse(gen(CrowdCounting(request ), request), content_type='multipart/x-mixed-replace; boundary=frame')

@login_required(login_url = '/')
def startRecordingCrowdCounting(request):
    if request.method == 'POST':
        if Recording.objects.filter(user= request.user.id, name= 'crowd_counting').exists():
            Recording.objects.filter(name= 'crowd_counting').update(is_recording= True)
        else:
            record = Recording.objects.create(
                name= 'crowd_counting',
                is_recording= True,
                user= authUser.objects.get(id= request.user.id)
            ).save()

        if request.POST['ipaddress'] != '':
            ip = request.POST['ipaddress']

        if IP_address.objects.filter(user= request.user.id, name= 'crowd_counting').exists():
            IP_address.objects.filter(user= request.user.id, name= 'crowd_couting').update(ip_address= ip)
        else:
            IP_address.objects.create(
                user= authUser.objects.get(id= request.user.id),
                name= 'crowd_counting',
                ip_address= ip
            ).save()

        return redirect('/crowdCountingView/')

@login_required(login_url = '/')
def stopRecordingCrowdCounting(request):
    Recording.objects.filter(name= 'crowd_counting').update(is_recording= False)
    destroy(CrowdCounting(request))
    return redirect('/crowdCountingView/')

@login_required(login_url = '/')
def crowdCountingView(request):
    user = user_data(request)
    return render(request, 'crowd.html', user)

@login_required(login_url = '/')
def socialDistancingView(request):
    user = user_data(request)
    return render(request, 'social.html', user)

# @login_required(login_url = '/')
def social_distancing(request):
    return StreamingHttpResponse(gen(SocialDistancing(request), request), content_type='multipart/x-mixed-replace; boundary=frame')

@login_required(login_url = '/')
def startRecordingSocialDistancing(request):
    if request.method == 'POST':
        if Recording.objects.filter(user= request.user.id, name= 'social_distancing').exists():
            Recording.objects.filter(name= 'social_distancing').update(is_recording= True)
        else:
            record = Recording.objects.create(
                name= 'social_distancing',
                is_recording= True,
                user= authUser.objects.get(id= request.user.id)
            ).save()

        if request.POST['ipaddress'] != '':
            ip = request.POST['ipaddress']
        
        if IP_address.objects.filter(user= request.user.id, name= 'social_distancing').exists():
            IP_address.objects.filter(user= request.user.id, name= 'social_distancing').update(ip_address= ip)
        else:
            IP_address.objects.create(
                user= authUser.objects.get(id= request.user.id),
                name= 'social_distancing',
                ip_address= ip
            ).save()

        return redirect('/socialDistancingView/')

# @login_required(login_url = '/')
@csrf_exempt
def stopRecordingSocialDistancing(request):
    Recording.objects.filter(name= 'social_distancing').update(is_recording= False)
    destroy(SocialDistancing(request))
    return redirect('/socialDistancingView/')

@login_required(login_url = '/')
def logout_view(request):
    logout(request)
    return redirect('/')

def landing(request):
    return render(request, 'landing.html')
