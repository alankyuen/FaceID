import cv2, sys, time, os, uuid, json
import numpy as np
import logging as log
import datetime as dt
from blob_store import*
from azure_face_api import *

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
cascPath = "haarcascade_frontalface_alt2.xml"
faceCascade = cv2.CascadeClassifier(cascPath)

#accessing webcam
video_capture = cv2.VideoCapture(0)

#display text font settings
font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10,450)
fontScale              = 1
fontColor              = (255,255,255)
lineType               = 2

#stabilization states (face_rect history and MSE)
detects_history = []
mse = 0
mse_cutoff = 250
stabilization_cutoff = 10.0 #number of "good" detects to take picture
decay_rate = 0.25 #time(secs) to decay detects_history by 1 (bigger value for lower decay rate)
min_neighbors = 3

#rect variable initialization
x = y = w = h = 0

#collect timestamp for stabailization decay
time_stamp = time.time()

#registration variables
student_name = ""
student_id = ""
student_email = ""
num_faces_taken = 0
num_faces_to_be_taken = 10

#user input
agreement = input("Photo Release Waiver (We won't post anything publically, we just want to be safe)\nDo you agree to release your photos? (y/n) ")
student_name = input("Name: ")
student_id = input("Student ID: ")
student_email = input("Student Email: ")
print("Face Registration Instructions: \n\t1. Take off any face accessories(glasses)\n\t2.Allow the software to take 10 pictures of your face at various angles and expressions (try different faces!!)\n\t3. Have fun!")

#fanc-ayee
for i in [3,2,1]:
    time.sleep(1)
    print("{}...".format(i))
time.sleep(2)

while num_faces_taken < num_faces_to_be_taken:

    if not video_capture.isOpened():
        print('Unable to load camera.')
        time.sleep(5)
        pass

    #Detect Faces
    ret, frame = video_capture.read()
    faces = faceCascade.detectMultiScale(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        scaleFactor=1.1,
        minNeighbors=min_neighbors,
        minSize=(100, 100)
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
    if(time.time() - time_stamp > decay_rate):
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
        if(mse > mse_cutoff):
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
    percent_stabilization = len(detects_history)/stabilization_cutoff
    if(percent_stabilization >= 1):
        cv2.imwrite("face_"+student_id+"_"+str(num_faces_taken)+".jpg",frame)
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
for i in range(10):
    file_name = "face_"+student_id+"_"+str(i)+".jpg"
    full_path_to_file = os.getcwd()+"/"+file_name
    url = bs.upload_file(file_name,full_path_to_file)
    student["face_urls"].append(url)

#initialize group access
csclub_group = personGroup()

#add person to group
personId = csclub_group.add_person(personName = student_name, studentId = student_id, studentEmail= student_email)
student["personId"] = personId

#add faces to person
csclub_group.add_faces(personId = personId, face_urls = student["face_urls"])

#save data
csclub_group.destruct()

#write student data to file
saved_data = {}
infile = open(os.path.join(os.getcwd(),"students.txt"),"r")
if(len(infile.read()) != 0):
    infile.seek(0)
    saved_data = json.load(infile)
saved_data[student_id] = student
infile.close()
with open(os.path.join(os.getcwd(),"students.txt"),"w") as outfile:
    json.dump(saved_data, outfile, indent = 4)


