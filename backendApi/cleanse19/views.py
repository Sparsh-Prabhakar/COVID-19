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
from django.contrib.auth.models import User
from django.contrib import messages

from .camera import *
from .models import *
from .serializers import *

from django.conf import settings
from django.core.mail import send_mail

# Create your views here.

@login_required(login_url = '/')
def getPeopleCount(request):
    if request.method == 'GET':
        people_count = Crowd_counting.objects.filter(user= request.user.id)
        return JsonResponse(people_count) 

@login_required(login_url = '/')
def getFaceMaskViolationsCount(request):
    if request.method == 'GET':
        violations = Face_mask.objects.filter(user= request.user.id)
        return JsonResponse(violations)

@login_required(login_url= '/')
def getSocialDistancingViolationsCount(request):
    if request.method == 'GET':
        violations = Social_distancing.objects.filter(user= request.user.id)
        return JsonResponse(violations)


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
        print(ip)
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

@login_required(login_url= '/')
def profile(request):
    return render(request,'profile.html')

@login_required(login_url= '/')
def profile_save(request):
    u = User.objects.get(id=request.user.id)
    if request.method == 'POST' :
        if request.POST['first_name']!='':
            first_name=request.POST['first_name']
        else:
            first_name= u.first_name

        if request.POST['last_name']!='':
            last_name=request.POST['last_name']
        else:
            last_name= u.last_name

        if request.POST['username']!='':
            username=request.POST['username']
            if User.objects.filter(username=username).exists():
                messages.info(request,'Username exists')
                return redirect('profile')
        else:
            username= u.username

        email=request.POST['email']
        
        if request.POST['email']!='':
            email=request.POST['email']
            if User.objects.filter(email=email).exists():
                messages.info(request,'Existing email')
                return redirect('profile')
        else:
            email= u.email
        
        u.first_name = first_name
        u.last_name = last_name
        u.username = username
        u.email=email
        u.save()
        return redirect('profile')
    # return render(request,'home.html')

@login_required(login_url= '/')
def help(request):
    return render(request,'help.html')

@login_required(login_url= '/')
def send_email(request):
    if request.method == 'POST' :
        subject=request.POST['subject']
        message=request.POST['message']
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ['cleanse19.app@gmail.com']
        send_mail(subject, message, email_from, recipient_list)
        return render(request,'home.html')

@login_required(login_url= '/')
def analysis(request):
    if request.method == 'GET':
        face_mask_violations = FaceMaskAnalysis.objects.filter(user= request.user.id)
        social_distancing_violations = SocialDistancingAnalysis.objects.filter(user= request.user.id)
        people_count = CrowdCountingAnalysis.objects.filter(user= request.user.id)

        face_dates = []
        face = {}
        for i in face_mask_violations:
            if i.timestamp.strftime("%x") not in face_dates:
                face[i.timestamp.strftime("%x")] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                face[i.timestamp.strftime('%x')][int(i.timestamp.strftime('%H'))] = i.violations
                face_dates.append(i.timestamp.strftime("%x"))
            else:
                if i.violations > face[i.timestamp.strftime('%x')][int(i.timestamp.strftime('%H'))]:
                    face[i.timestamp.strftime("%x")][int(i.timestamp.strftime('%H'))] = i.violations

        social_dates = []
        social = {}
        for i in social_distancing_violations:
            if i.timestamp.strftime("%x") not in social_dates:
                social[i.timestamp.strftime("%x")] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                social[i.timestamp.strftime('%x')][int(i.timestamp.strftime('%H'))] = i.violations
                social_dates.append(i.timestamp.strftime("%x"))
            else:
                if i.violations > social[i.timestamp.strftime('%x')][int(i.timestamp.strftime('%H'))]:
                    social[i.timestamp.strftime("%x")][int(i.timestamp.strftime('%H'))] = i.violations

        people_dates = []
        people = {}
        for i in people_count:
            if i.timestamp.strftime("%x") not in people_dates:
                people[i.timestamp.strftime("%x")] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                people[i.timestamp.strftime('%x')][int(i.timestamp.strftime('%H'))] = i.violations
                people_dates.append(i.timestamp.strftime("%x"))
            else:
                if i.violations > people[i.timestamp.strftime('%x')][int(i.timestamp.strftime('%H'))]:
                    people[i.timestamp.strftime("%x")][int(i.timestamp.strftime('%H'))] = i.violations
        
        print(face)
        return render(request,'analysis.html')