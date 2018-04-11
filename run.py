import cv2, sys, time, os, uuid, json
import numpy as np
import logging as log
import datetime as dt
from azure_face_api import *
from blob_store import *

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

bs = blob_store()
csclub_group = personGroup()

#load log
log_path = os.path.join(*[CURR_DIR,"logs","login.txt"])
log = open(log_path,"a")

#loading haarcascade
cascPath = os.path.join(*[CURR_DIR, "models","haarcascade_frontalface_alt2.xml"])
faceCascade = cv2.CascadeClassifier(cascPath)

#accessing webcam
video_capture = cv2.VideoCapture(0)
VIDEO_WIDTH = int(video_capture.get(3))  # float
VIDEO_HEIGHT = int(video_capture.get(4)) # float

#display text font settings
font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10,450)
fontScale              = 1
fontColor              = (255,255,255)
lineType               = 2

#face detect variables
config_data = json.load(open(os.path.join(CURR_DIR, "config.txt"), "r"))
MSE_CUTOFF = config_data["mse_cutoff"] #error margin
STABILIZATION_CUTOFF = config_data["stabilization_cutoff"] #number of "good" detects to take picture
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

	#calculate percent stabilization, 0 is unstable, 1 is stable
	percent_stabilization = len(detects_history)/STABILIZATION_CUTOFF
	if(percent_stabilization >= 1):
		#generate uuid filename and path
		file_name = str(uuid.uuid4())+".jpg"
		full_path_to_file = os.path.join(*[CURR_DIR,"img",file_name])

		#save image and upload to blob storage
		cv2.imwrite(full_path_to_file,equ)
		url = bs.upload_file(file_name,full_path_to_file)
		os.remove(full_path_to_file)

	    #identify
		likely_face = csclub_group.faceDetect(url)
		
		if(likely_face != None):
			face_id = likely_face["faceId"]
			age = str(likely_face["faceAttributes"]["age"])
			gender = str(likely_face["faceAttributes"]["gender"])
			smile = str(likely_face["faceAttributes"]["smile"])

			person = csclub_group.faceIdentify( faceIds = [face_id], maxNumOfCandidates = 10, confidenceThreshold = 0.5 )
			timestamp = time.time()
			
			# if(person_id == ""):
			# 	display_text = "Person Not Identifiable"
			# 	print(display_text)

			# 	cv2.rectangle(frame, (0,0), (375,70), (0, 0, 0), -1)#% display
			# 	cv2.putText(frame, display_text , (10,40), font, 1, (0,0,255), 3)

			# 	#cv2.imshow('validation', frame[y:y+h,x:x+w])

			if(person != ""):
				person_id = person["personId"]
				confidence_id = person["confidence"]


				name = csclub_group.persons[person_id]['name']
				studentId = csclub_group.persons[person_id]['studentId']
				email = csclub_group.persons[person_id]['email']
				login_timestamp = dt.datetime.utcnow().strftime("%b-%d:%H:%M:%S")

				log_string = "\t".join([login_timestamp, name, studentId, gender, smile])
				print("[Logging] -- {}".format(log_string))
				log.write(log_string+"\n")

				cv2.rectangle(frame, (0,VIDEO_HEIGHT//3), (VIDEO_WIDTH,(VIDEO_HEIGHT*2)//3), (0, 0, 0), -1)
				cv2.putText(frame, "[SUCCESS] <CompSciClub>" , (25 , (VIDEO_HEIGHT//2) - 35), font, 1, (0,255,0), 1)
				cv2.putText(frame, "WELCOME {}!!".format(name) , (25 , (VIDEO_HEIGHT//2)), font, 1, (255,255,255), 2)
				cv2.putText(frame, "Age-[{}] Gender-[{}] Smile:)-[{}]".format(age,gender,smile) , (25, (VIDEO_HEIGHT//2)+35), font, 0.8, (255,255,255), 1)
				#cv2.putText(frame, "Email: {}".format(email) , (x,y+60), font, 0.25, (255,255,255), 1)
				cv2.imshow('Video', frame)
				cv2.waitKey(6000)

		detects_history = []
		percent_stabilization = 0.0

    #visuals
	cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3) #face bounding box

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

#close log
log.close()