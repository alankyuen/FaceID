#person group initialization
from azure_face_api import *

def createPersonGroup(name):
	group = personGroup(name)
	group.createPersonGroup(name, "0000")
	group.destruct()

def deletePersonGroup(name):
	group = personGroup(name):
	group.deletePersonGroup()
	#need to delete persongroup from data.txt

new_club_name = ""
#createPersonGroup(new_club_name)
