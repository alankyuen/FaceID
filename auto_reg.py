import cv2, sys, time, os, uuid, json
import numpy as np
import logging as log
import datetime as dt
from blob_store import*
from azure_face_api import *

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

#words of encouragement
encouragement = ["Let's see what you got!",
                 "Great job!",
                 "Beautiful!",
                 "Amazing!!!",
                 "Keep it up!",
                 "** Super-Star **",
                 "Wonderful!!",
                 "CUTE!!",
                 "Almost there!!",
                 "Last one!!",
                 "Nicely done!!"]

#loading haarcascade
cascPath =  os.path.join(*[CURR_DIR, "models","haarcascade_frontalface_alt2.xml"])
faceCascade = cv2.CascadeClassifier(cascPath)

#accessing webcam
video_capture = cv2.VideoCapture(0)

#display text font settings
font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10,450)
fontScale              = 1
fontColor              = (255,255,255)
lineType               = 2

#face detect variables
config_infile = open(os.path.join(CURR_DIR, "config.txt"), "r")
config_data = json.load(config_infile)
MSE_CUTOFF = config_data["mse_cutoff"] #error margin
STABILIZATION_CUTOFF = config_data["stabilization_cutoff"] #number of "good" detects to take picture
DECAY_RATE = config_data["decay_rate"] #time(secs) to decay detects_history by 1 (bigger value for lower decay rate)
SCALE_FACTOR = config_data["scaleFactor"]
MIN_NEIGHBORS = config_data["min_neighbors"] # [<<] for softer detect [>>] for harder detect
MIN_SIZE = tuple(config_data["minSize"]) #min size for detect bounding box

#variable initialization
detects_history = []
mse = 0
x = y = w = h = 0 #rect 

#collect timestamp for stabailization decay
time_stamp = time.time()

#registration variables
student_name = ""
student_id = ""
student_email = ""
num_faces_taken = 0
num_faces_to_be_taken = 10
picture_fnames = []

#initialize group access
csclub_group = personGroup()

#user input
agreement = input("Photo Release Waiver (We won't post anything publically, we just want to be safe)\nDo you agree to release your photos? (y/n) ")
student_name = input("Name: ")
student_id = input("Student ID: ")
student_email = input("Student Email: ")
print("Face Registration Instructions: \n\t1. You might need to take off glasses/hat\n\t2.Allow the software to take 10 pictures of your face at various angles and expressions (try different faces!!)\n\t3. Have fun!")

#fanc-ayee
for i in [3,2,1]:
    time.sleep(1)
    print("{}...".format(i))
time.sleep(2)

#display video size
cv2.namedWindow('Video', cv2.WINDOW_NORMAL)

while num_faces_taken < num_faces_to_be_taken:

    if not video_capture.isOpened():
        print('Unable to load camera.')
        time.sleep(5)
        pass

    #Detect Faces
    ret, frame = video_capture.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    equ = clahe.apply(gray)
    #frame = equ
    faces = faceCascade.detectMultiScale(
        equ,
        scaleFactor = SCALE_FACTOR,
        minNeighbors = MIN_NEIGHBORS,
        minSize = MIN_SIZE
    )

    #retrieve biggest face
    largest_area = 0
    main_face_rect = []
    for (x, y, w, h) in faces:
        area = w * h
        if(area > largest_area):
            largest_area = area
            main_face_rect = [x,y,w,h]

    #stabilization decay
    if(time.time() - time_stamp > DECAY_RATE):
        time_stamp = time.time()
        if(len(detects_history) > 0):
            detects_history.pop(0)

    #if face is detected, calculate stabilization variables
    if(largest_area > 0):
        x = main_face_rect[0]
        y = main_face_rect[1]
        w = main_face_rect[2]
        h = main_face_rect[3]
        
        #calculate current face's MSE from history
        detects_history.append(main_face_rect)
        average_history = np.average(detects_history,axis=0)
        mse = np.mean((np.array(main_face_rect) - average_history)**2)

        #if MSE is > cutoff, reset history
        if(mse > MSE_CUTOFF):
            detects_history = []
        
        # if len(detects_history) < 25:
        # else:
        #     #x[:-1] = x[1:]; x[-1] = newvalue
        #     detects_history[:-1] = detects_history[1:]
        #     detects_history[-1] = main_face_rect

        #     average_history = np.average(detects_history,axis=0)
        #     mse = np.mean((np.array(main_face_rect) - average_history)**2)

        #     if(mse > mse_cutoff):
        #         detects_history = []

    #calculate percent stabilization, 0 is unstable, 1 is stable
    percent_stabilization = len(detects_history)/STABILIZATION_CUTOFF
    if(percent_stabilization >= 1):

        #get user validation
        cv2.imshow('validation', frame[y:y+h,x:x+w])

        #save picture
        img_fname = "face_"+student_id+"_"+str(uuid.uuid4())+".jpg"
        picture_fnames.append(img_fname)
        cv2.imwrite(os.path.join(*[CURR_DIR,"img",img_fname]), frame[y:y+h,x:x+w])

        #reset detection variables
        detects_history = []
        percent_stabilization = 0.0
        num_faces_taken += 1

    #visuals
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2) #face bounding box

    cv2.rectangle(frame, (5,480), (140,420), (0, 0, 0), -1)#% display
    display_text = ("[{0:.3}%]".format(percent_stabilization*100))
    cv2.putText(frame, display_text , bottomLeftCornerOfText, font, fontScale, (0,percent_stabilization*255,(1-percent_stabilization)*255), lineType)

    display_text = ("# Pics: {}/{}".format(num_faces_taken,num_faces_to_be_taken))
    cv2.putText(frame, display_text, (400,450), font, fontScale, fontColor, lineType)

    display_text = encouragement[num_faces_taken]
    cv2.putText(frame, display_text, (10,50), font, fontScale + (num_faces_taken/num_faces_to_be_taken), (0,0,0), 3)

    # Display the resulting frame

    cv2.imshow('Video', frame)
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()

#store images to obtain urls
student = {"name": student_name, "email":student_email, "face_urls":[]}
bs = blob_store()
for fname in picture_fnames:
    full_path_to_file = os.path.join(*[CURR_DIR,"img",fname])
    url = bs.upload_file( fname, full_path_to_file )
    student["face_urls"].append(url)
    os.remove(full_path_to_file)

if(student_id not in csclub_group.studentIds.keys()):
    #add person to group
    personId = csclub_group.add_person(personName = student_name, studentId = student_id, studentEmail= student_email)
    print("Sucessfully added personId {}".format(personId))
else:
    personId = csclub_group.studentIds[student_id]
    print("Welcome back {}/{}".format(student_name, csclub_group.persons[personId]['name']))
#add faces to person
csclub_group.add_faces(personId = personId, face_urls = student["face_urls"])
print("Sucessfully added faces to {}".format(personId))
#save data
csclub_group.destruct()

