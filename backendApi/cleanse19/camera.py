import os
import urllib.request

import cv2
import numpy as np
from django.conf import settings
from django.contrib.auth.models import User as authUser
from imutils.video import VideoStream
from imutils.video import FPS 
import imutils
import time
import dlib

from .centroidtracker import *
from .trackableobject import *
from .models import *
from .detection import *


class FaceMaskDetection(object):
    def __init__(self):
        self.url = 'http://192.168.1.101:8080/shot.jpg'

    def delete(self):
        cv2.destroyAllWindows()

    def get_frame(self, request):
        imgResp = urllib.request.urlopen(self.url)
        imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgNp, 1)

        classes = []
        with open("/home/sparsh/COVID-19/face/classes.txt", "r") as f:
            classes = f.read().splitlines()

        height, width, _ = img.shape

        font = cv2.FONT_HERSHEY_PLAIN

        net = cv2.dnn.readNet('/home/sparsh/COVID-19/face/yolov3_training_last.weights', '/home/sparsh/COVID-19/face/yolov3_testing.cfg')

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
                # cv2.putText(frame_flip, label + " " + confidence, (x, y+20), font, 2, (255,255,255), 2)

        if Face_mask.objects.filter(user= 1).exists():
            Face_mask.objects.filter(user= 1).update(violations= count)
        else:
            user = authUser.objects.get(id= 1)       
            face = Face_mask.objects.create(
                user= user,
                violations= count
            )                
            face.save()
            

        resize = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LINEAR)
        frame_flip = cv2.flip(resize, 1)

        ret, jpeg = cv2.imencode('.jpg', frame_flip)

        return jpeg.tobytes()
    
class CrowdCounting(object):
    def __init__(self):
        self.url = 'http://192.168.1.101:8080/shot.jpg'

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

        net = cv2.dnn.readNetFromCaffe('/home/sparsh/COVID-19/people counting/mobilenet_ssd/MobileNetSSD_deploy.prototxt', '/home/sparsh/COVID-19/people counting/mobilenet_ssd/MobileNetSSD_deploy.caffemodel')

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

        if Crowd_counting.objects.filter(user= 1).exists():
            Crowd_counting.objects.filter(user= 1).update(people_count= people_inside)
        else:
            user = authUser.objects.get(id= 1)       
            crowd = Crowd_counting.objects.create(
                user= user,
                people_count= people_inside
            )                
            crowd.save()

             
        resize = cv2.resize(frame, (640, 480), interpolation= cv2.INTER_LINEAR)
        ret, jpeg = cv2.imencode('.jpg', frame)

        return jpeg.tobytes()

class SocialDistancing(object):
    def __init__(self):
        self.url = 'http://192.168.1.101:8080/shot.jpg'

    def delete(self):
        cv2.destroyAllWindows()

    def get_frame(self, request):
        imgResp = urllib.request.urlopen(self.url)
        imgNp = np.array(bytearray(imgResp.read()), dtype= np.uint8)
        frame = cv2.imdecode(imgNp, 1)

        labels = ['person', 'bicycle', 'car', 'motorbike', 'aeroplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'sofa', 'pottedplant', 'bed', 'diningtable', 'toilet', 'tvmonitor', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

        net = cv2.dnn.readNetFromDarknet('/home/sparsh/COVID-19/social distancing/social-distancing-detector-master/yolo-coco/yolov3.cfg', '/home/sparsh/COVID-19/social distancing/social-distancing-detector-master/yolo-coco/yolov3.weights')

        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        frame = imutils.resize(frame, width=640)
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

        if Social_distancing.objects.filter(user= 1).exists():
            Social_distancing.objects.filter(user= 1).update(violations= len(violate))
        else:
            user = authUser.objects.get(id= 1)       
            crowd = Social_distancing.objects.create(
                user= user,
                violations= len(violate)
            )                
            crowd.save()


        resize = cv2.resize(frame, (640, 480), interpolation= cv2.INTER_LINEAR)
        ret, jpeg = cv2.imencode('.jpg', frame)

        return jpeg.tobytes()