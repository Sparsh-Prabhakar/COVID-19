import cv2, os, urllib.request
import numpy as np
from django.contrib.auth.models import User as authUser
from django.conf import settings

from .models import *

class FaceMaskDetection(object):
    def __init__(self):
        self.url = 'http://192.168.1.101:8080/shot.jpg'

    def __del__(self):
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
    