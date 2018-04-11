import cv2, sys, time, os, uuid, json
import numpy as np
import logging as log
import datetime as dt
from azure_face_api import *
from blob_store import *

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

bs = blob_store()
csclub_group = personGroup()

#loading haarcascade
cascPath = os.path.join(*[CURR_DIR, "models","haarcascade_frontalface_alt2.xml"])
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
config_data = json.load(open(os.path.join(CURR_DIR, "config.txt"), "r"))
MSE_CUTOFF = config_data["mse_cutoff"]*1.25 #error margin
STABILIZATION_CUTOFF = config_data["stabilization_cutoff"]/2 #number of "good" detects to take picture
DECAY_RATE = config_data["decay_rate"] #time(secs) to decay detects_history by 1 (bigger value for lower decay rate)
SCALE_FACTOR = config_data["scaleFactor"]
MIN_NEIGHBORS = config_data["min_neighbors"] # [<<] for softer detect [>>] for harder detect
MIN_SIZE =  tuple(config_data["minSize"]) #min size for detect bounding box

#variable initialization
detects_history = []
mse = 0
x = y = w = h = 0 #rect 

#collect timestamp for stabailization decay
time_stamp = time.time()

while True:

	if not video_capture.isOpened():
	    print('Unable to load camera.')
	    time.sleep(5)
	    pass

	#Detect Faces
	ret, frame = video_capture.read()
	faces = faceCascade.detectMultiScale(
	    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
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

	#calculate percent stabilization, 0 is unstable, 1 is stable
	percent_stabilization = len(detects_history)/STABILIZATION_CUTOFF
	if(percent_stabilization >= 1):
		file_name = str(uuid.uuid4())+".jpg"
		cv2.imwrite(file_name,frame)
		full_path_to_file = os.path.join(*[CURR_DIR,"img",file_name])
		url = bs.upload_file(file_name,full_path_to_file)
		os.remove(full_path_to_file)
	    #identify
		face_id = csclub_group.faceDetect(url)
		if(face_id != ""):
			person_id = csclub_group.faceIdentify( faceIds = [face_id], maxNumOfCandidates = 10, confidenceThreshold = 0.5 )
			time.sleep(3)
			timestamp = time.time()
			
			if(person_id == ""):
				display_text = "Person Not Identifiable"
				print(display_text)

				cv2.rectangle(frame, (0,0), (375,70), (0, 0, 0), -1)#% display
				cv2.putText(frame, display_text , (10,40), font, 1, (0,0,255), 3)

				cv2.imshow('Video', frame)
				cv2.waitKey(3000)
			else:
				name = csclub_group.persons[person_id]['name']
				studentId = csclub_group.persons[person_id]['studentId']
				email = csclub_group.persons[person_id]['email']
				
				cv2.rectangle(frame, (0,0), (400,140), (0, 0, 0), -1)#% display
				cv2.putText(frame, "Name: {}".format(name) , (10,40), font, 1, (255,255,255), 2)
				cv2.putText(frame, "studentId: {}".format(studentId) , (10,80), font, 1, (255,255,255), 2)
				cv2.putText(frame, "email: {}".format(email) , (10,120), font, 1, (255,255,255), 2)
				cv2.imshow('Video', frame)
				cv2.waitKey(3000)

		

		detects_history = []
		percent_stabilization = 0.0

    #visuals
	cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2) #face bounding box

	cv2.rectangle(frame, (5,480), (140,420), (0, 0, 0), -1)#% display
	display_text = ("[{0:.3}%]".format(percent_stabilization*100))
	cv2.putText(frame, display_text , bottomLeftCornerOfText, font, fontScale, (0,percent_stabilization*255,(1-percent_stabilization)*255), lineType)

	# Display the resulting frame
	cv2.imshow('Video', frame)

	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()