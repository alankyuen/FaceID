import cv2, sys, time, os, uuid, json, random
import numpy as np
import logging as log
import datetime as dt
from blob_store import*
from azure_face_api import *

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


def add_faces(group, student_id, face_urls):
	personId = group.studentIds[student_id]
	group.add_faces(personId = personId, face_urls = face_urls)

def add_person(group, student_json):
	name = student_json["name"]
	student_id = student_json["student_id"]
	student_email = student_json["student_email"]
	personId = group.add_person( personName = name, studentId = student_id, studentEmail = student_email )
	return personId

#create group object
csclub_group = personGroup()

#add alan faces to already existing person
alan_student_id = "79616"
add_faces(csclub_group, alan_student_id, alan_urls)

#add persons and their faces
for i in range(len(persons)):
	print("Adding {}".format(persons[i]))

	person_json = {"name":persons[i], "student_id": "".join([str(random.randint(0,9)) for i in range(7)]), "student_email": ""}
	person_json["student_email"] = persons[i] + person_json["student_id"] + "@ivc.edu"

	if(person_json["student_id"] not in csclub_group.studentIds.keys()):
		personId = add_person(csclub_group, person_json)
	else:
		personId = csclub_group.studentIds[person_json["student_id"]]

	add_faces(csclub_group, person_json["student_id"], face_urls[i])
	
csclub_group.destruct()


	

