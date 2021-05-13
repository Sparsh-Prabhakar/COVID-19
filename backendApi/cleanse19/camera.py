import os
import time
import urllib.request

import cv2
from django.core.checks import messages
import dlib
import imutils
import numpy as np
import datetime
from django.conf import settings
from django.contrib.auth.models import User as authUser
from django.utils.timezone import make_aware
from django.core.mail import send_mail
from imutils.video import FPS, VideoStream

from .centroidtracker import *
from .config import *
from .detection import *
from .models import *
from .trackableobject import *


class FaceMaskDetection(object):
    def __init__(self, request):
        ip = IP_address.objects.filter(user= request.user.id, name= 'face_mask')
        ip = ip[0].ip_address + '/shot.jpg'
        self.url = ip
        self.counter = 0

    def delete(self):
        cv2.destroyAllWindows()

    def get_frame(self, request):
        imgResp = urllib.request.urlopen(self.url)
        imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgNp, 1)

        classes = []
        with open(face_classes, "r") as f:
            classes = f.read().splitlines()

        height, width, _ = img.shape

        font = cv2.FONT_HERSHEY_PLAIN

        net = cv2.dnn.readNet(face_weights, face_cfg)

        blob = cv2.dnn.blobFromImage(img, 1/255, (416, 416), (0,0,0), swapRB=True, crop=False)
        net.setInput(blob)
        output_layers_names = net.getUnconnectedOutLayersNames()
        layerOutputs = net.forward(output_layers_names)

        boxes = []
        confidences = []
        class_ids = []

        count = 0

        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.2:
                    center_x = int(detection[0]*width)
                    center_y = int(detection[1]*height)
                    w = int(detection[2]*width)
                    h = int(detection[3]*height)

                    x = int(center_x - w/2)
                    y = int(center_y - h/2)

                    boxes.append([x, y, w, h])
                    confidences.append((float(confidence)))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.2, 0.4)

        count = 0
        if len(indexes)>0:
            for i in indexes.flatten():
                
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                confidence = str(round(confidences[i],2))
                if label == 'mask':
                    color = (0, 255, 0)
                else:
                    count += 1
                    color = (0, 0, 255)
                cv2.rectangle(img, (x,y), (x+w, y+h), color, 2)
                

        if Face_mask.objects.filter(user= request.user.id).exists():
            Face_mask.objects.filter(user= request.user.id).update(violations= count)
        else:
            user = authUser.objects.get(id= request.user.id)       
            face = Face_mask.objects.create(
                user= user,
                violations= count
            )                
            face.save()


        max_count = Crowd_counting.objects.filter(user= request.user.id)[0].max_count
        max_face_violations = int(max_count/10)

        if count > max_face_violations:
            last_mail_time = Face_mask.objects.filter(user= request.user.id)[0].last_mail_time
            if last_mail_time + datetime.timedelta(minutes=15) < make_aware(datetime.datetime.now()):
                message = 'Face Mask Violations are increasing! Please take the necessary actions.\nCurrent count of people not wearing mask properly: {}'.format(count)
                email_from = settings.EMAIL_HOST_USER
                subject = 'People not wearing masks properly!'
                recipient_list = [request.user.email]
                send_mail(subject, message, email_from, recipient_list)


        self.counter += 1
        if self.counter == 10:
            FaceMaskAnalysis.objects.create(
                user= authUser.objects.get(id= request.user.id),
                violations= count
            ).save()
            self.counter = 0
            

        resize = cv2.resize(img, (1000, 700), interpolation=cv2.INTER_LINEAR)
        frame_flip = cv2.flip(resize, 1)
        text = "Face Mask Violations: {}".format(count)
        cv2.putText(frame_flip, text, (10, frame_flip.shape[0] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

        ret, jpeg = cv2.imencode('.jpg', frame_flip)

        return jpeg.tobytes()
    
class CrowdCounting(object):
    def __init__(self, request):
        ip = IP_address.objects.filter(user= request.user.id, name= 'crowd_counting')
        ip = ip[0].ip_address + '/shot.jpg'
        self.url = ip
        self.counter = 0

    def delete(self):
        cv2.destroyAllWindows()

    def get_frame(self, request):
        classes = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]

        imgResp = urllib.request.urlopen(self.url)
        # imgResp = cv2.VideoCapture('/home/sparsh/COVID-19/people counting/videos/example_01.mp4')
        # imgResp = urllib.request.urlopen('file:///home/sparsh/COVID-19/people counting/videos/example_01.mp4')
        imgNp = np.array(bytearray(imgResp.read()), dtype= np.uint8)
        frame = cv2.imdecode(imgNp, 1)

        net = cv2.dnn.readNetFromCaffe(crowd_prototxt, crowd_caffemodel)

        W = None
        H = None

        ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
        trackers = []
        trackableObjects = {}

        totalFrames = 0
        people_inside = 0

        fp = FPS()
        fps = fp.start()
        frame = imutils.resize(frame, width= 500)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        (H, W) = frame.shape[:2]

        status = 'Waiting'
        rects = []
        
        if totalFrames % 30 == 0:
            status = 'Detecting'
            trackers = []

            blob = cv2.dnn.blobFromImage(frame, 1/255, (416, 416), (0,0,0), swapRB=True, crop=False)
            net.setInput(blob)
            detections = net.forward()

            for i in np.arange(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]

                if confidence > 0.4:
                    idx = int(detections[0, 0, i, 1])
                    if classes[idx] != "person":
                        continue

                    box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                    (startX, startY, endX, endY) = box.astype("int")

                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(startX, startY, endX, endY)
                    tracker.start_track(rgb, rect)

                    trackers.append(tracker)

        else:
            for tracker in trackers:
                status = 'Tracking'

                tracker.update(rgb)
                pos = tracker.get_position()

                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())

                rects.append((startX, startY, endX, endY))

        cv2.line(frame, (0, H // 2), (W, H // 2), (0, 255, 255), 2)
        objects = ct.update(rects)

        for (objectID, centroid) in objects.items():
            to = trackableObjects.get(objectID, None)

            if to is None:
                to = TrackableObject(objectID, centroid)
            else:
                y = [c[1] for c in to.centroids]
                direction = centroid[1] - np.mean(y)
                to.centroids.append(centroid)

                if not to.counted:
                    if direction < 0 and centroid[1] < H // 2:
                        people_inside -= 1 
                        to.counted = True
                    elif direction > 0 and centroid[1] > H // 2:
                        people_inside += 1
                        to.counted = True
            trackableObjects[objectID] = to

        info = [ ("People inside", people_inside), ("Status", status)]

        for (i, (k, v)) in enumerate(info):
            text = "{}: {}".format(k, v)
            cv2.putText(frame, text, (10, H - ((i * 20) + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if Crowd_counting.objects.filter(user= request.user.id).exists():
            Crowd_counting.objects.filter(user= request.user.id).update(people_count= people_inside)
        else:
            user = authUser.objects.get(id= request.user.id)       
            crowd = Crowd_counting.objects.create(
                user= user,
                people_count= people_inside
            )                
            crowd.save()

        max_count_tuple = Crowd_counting.objects.filter(user= request.user.id)
        max_count = max_count_tuple[0].max_count

        if max_count != 0:
            if  people_inside > max_count:
                last_mail_time = Crowd_counting.objects.filter(user= request.user.id)[0].last_mail_time    
                if last_mail_time + datetime.timedelta(minutes= 15) < make_aware(datetime.datetime.now()):
                    message = 'The max_count has been exceeded. Please take the required actions.\nCurrent Count: {count}'.format(count= people_inside)
                    email_from = settings.EMAIL_HOST_USER
                    subject = 'Maximum Count has been exceeded!'
                    recipient_list = [request.user.email]
                    send_mail(subject, message, email_from, recipient_list)
                    Crowd_counting.objects.filter(user= request.user.id).update(last_mail_time= make_aware(datetime.datetime.now()))

        self.counter += 1
        if self.counter == 10:
            CrowdCountingAnalysis.objects.create(
                user= authUser.objects.get(id= request.user.id),
                count= people_inside
            ).save()
            self.counter = 0
             
        resize = cv2.resize(frame, (1000, 700), interpolation= cv2.INTER_LINEAR)
        ret, jpeg = cv2.imencode('.jpg', frame)

        return jpeg.tobytes()

class SocialDistancing(object):
    def __init__(self, request):
        ip = IP_address.objects.filter(user= request.user.id, name= 'social_distancing')
        ip = ip[0].ip_address + '/shot.jpg'
        self.url = ip
        self.counter = 0

    def delete(self):
        cv2.destroyAllWindows()

    def get_frame(self, request):
        imgResp = urllib.request.urlopen(self.url)
        imgNp = np.array(bytearray(imgResp.read()), dtype= np.uint8)
        frame = cv2.imdecode(imgNp, 1)

        labels = ['person', 'bicycle', 'car', 'motorbike', 'aeroplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'sofa', 'pottedplant', 'bed', 'diningtable', 'toilet', 'tvmonitor', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

        net = cv2.dnn.readNetFromDarknet(social_cfg, social_weights)

        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        frame = imutils.resize(frame, width=1000, height= 700)
        results = detect_people(frame, net, ln, personIdx=labels[0])    

        violate = set()

        if len(results) >= 2:
            centroids = np.array([r[2] for r in results])
            D = dist.cdist(centroids, centroids, metric="euclidean")

            for i in range(0, D.shape[0]):
                for j in range(i+1, D.shape[1]):
                    if D[i, j] < 50:
                        violate.add(i)
                        violate.add(j)

        for (i, (prob, bbox, centroid)) in enumerate(results):
            (startX, startY, endX, endY) = bbox
            (cX, cY) = centroid
            color = (0, 255, 0)

            if i in violate:
                color = (0, 0, 255)
        
            cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
            cv2.circle(frame, (cX, cY), 5, color, 1)

        text = "Social Distancing Violations: {}".format(len(violate))
        cv2.putText(frame, text, (10, frame.shape[0] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

        if Social_distancing.objects.filter(user= request.user.id).exists():
            Social_distancing.objects.filter(user= request.user.id).update(violations= len(violate))
        else:
            user = authUser.objects.get(id= request.user.id)       
            social = Social_distancing.objects.create(
                user= user,
                violations= len(violate)
            )                
            social.save()

        max_count = Crowd_counting.objects.filter(user= request.user.id)[0].max_count
        max_social_violations = int(max_count/10)

        if len(violate) > max_social_violations:
            last_mail_time = Social_distancing.objects.filter(user= request.user.id)[0].last_mail_time
            if last_mail_time + datetime.timedelta(minutes=15) < make_aware(datetime.datetime.now()):
                message = 'Social Distancing Violations are increasing! Please take the necessary actions.\nCurrent violations: {}'.format(len(violate))
                email_from = settings.EMAIL_HOST_USER
                subject = 'People are getting closer!'
                recipient_list = [request.user.email]
                send_mail(subject, message, email_from, recipient_list)

        self.counter += 1
        if self.counter == 10:
            SocialDistancingAnalysis.objects.create(
                user= authUser.objects.get(id= request.user.id),
                violations= len(violate)
            ).save()
            self.counter = 0


        resize = cv2.resize(frame, (1000, 700), interpolation= cv2.INTER_LINEAR)
        ret, jpeg = cv2.imencode('.jpg', frame)

        return jpeg.tobytes()
