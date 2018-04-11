import cv2, sys, time, os, uuid, json
import numpy as np
import logging as log
import datetime as dt
from blob_store import*
from azure_face_api import *
"""
add fake people
"""
time.sleep(60)
persons = ["amal", "matthew", "lauren", "stella"]

face_urls = [["https://s7.postimg.org/enmb1tuhn/IMG_20180331_152302.jpg",
"https://s7.postimg.org/hvqseclqz/IMG_20180331_152303.jpg",
"https://s7.postimg.org/but3h9rez/IMG_20180331_152304.jpg",
"https://s7.postimg.org/mhmwmq257/IMG_20180331_152305.jpg"],
["https://s7.postimg.org/uadkep0ej/IMG_20180331_152321.jpg",
"https://s7.postimg.org/sikljtjmj/IMG_20180331_152321_1.jpg",
"https://s7.postimg.org/vcnqxa18b/IMG_20180331_152322.jpg",
"https://s7.postimg.org/3pb1j6nrf/IMG_20180331_152323.jpg",
"https://s7.postimg.org/rgaf1avob/IMG_20180331_152324.jpg",
"https://s7.postimg.org/c7khnj9pn/IMG_20180331_152324_1.jpg"],
["https://s7.postimg.org/c7khnkk0b/IMG_20180331_152351.jpg",
"https://s7.postimg.org/c7khnkrq3/IMG_20180331_152351_1.jpg",
"https://s7.postimg.org/x4gps8xgr/IMG_20180331_152352.jpg",
"https://s7.postimg.org/asiwyv62j/IMG_20180331_152353.jpg"],
["https://s7.postimg.org/i8i6kogx7/IMG_20180331_152450.jpg",
"https://s7.postimg.org/svbzq3hcr/IMG_20180331_152451.jpg",
"https://s7.postimg.org/6w5l2vssr/IMG_20180331_152451_1.jpg",
"https://s7.postimg.org/xh83ygibf/IMG_20180331_152452.jpg",
"https://s7.postimg.org/txm68nnbf/IMG_20180331_152453.jpg"]]

alan_urls = ["https://preview.ibb.co/f51oaS/download.jpg",
"https://preview.ibb.co/jnUPFS/webcam_toy_photo1.jpg",
"https://preview.ibb.co/f2Bt9n/webcam_toy_photo2.jpg",
"https://preview.ibb.co/gUNN27/webcam_toy_photo3.jpg"]

csclub_group = personGroup()

#add alan faces
alan_student_id = "796164"
alan_personId = csclub_group.studentIds[alan_student_id]
csclub_group.add_faces(personId = alan_personId, face_urls = alan_urls)

#load saved student data
saved_data = {}
infile = open(os.path.join(os.getcwd(),"students.txt"),"r")
if(len(infile.read()) != 0):
	infile.seek(0)
	saved_data = json.load(infile)
infile.close()

#add persons
for i in range(len(persons)):
	print(persons[i])
	personId = csclub_group.add_person(personName = persons[i], studentId = str(i), studentEmail= persons[i]+"@csc.org" )
	print(personId)
	csclub_group.add_faces(personId = personId, face_urls = face_urls[i])
	
	saved_data[student_id] = student
	
#write student data to file
with open(os.path.join(os.getcwd(),"students.txt"),"w") as outfile:
	json.dump(saved_data, outfile, indent = 4)

csclub_group.destruct()