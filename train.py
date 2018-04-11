import cv2, sys, time, os, uuid, json
import numpy as np
import logging as log
import datetime as dt
from blob_store import*
from azure_face_api import *

time.sleep(60)


csclub_group = personGroup()

#train personGroup
csclub_group.train()

# #get training status
training_status = csclub_group.get_trainingStatus()
while training_status != "succeeded":
  time.sleep(15)
  training_status = csclub_group.get_trainingStatus()
  


csclub_group.destruct()

