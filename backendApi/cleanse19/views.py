from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers


from .models import *
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