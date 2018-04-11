##########
# [init] #
##########

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json, time, os

class personGroup:

  def __init__(self):
    
    self.personGroupId = ""
    self.persons = {}
    self.studentIds = {}
    self.faces = {}
    
    #retrieve saved student data
    save_json_data = {}
    save_data_path = os.path.join(os.getcwd(), "data.txt")
    infile = open(save_data_path, "r")
    if(len(infile.read()) != 0):
      infile.seek(0)
      save_json_data = json.load(infile)
      self.personGroupId = list(save_json_data.keys())[0]
      self.persons = save_json_data[self.personGroupId]["persons"]
      self.studentIds = save_json_data[self.personGroupId]["studentIds"]
      self.faces = save_json_data[self.personGroupId]["faces"]
    infile.close()

    #get face_api service key and endpoint
    key_json = json.load(open(os.path.join(os.getcwd(), "azure_service_keys.txt"), "r"))
    KEY = key_json["face_api_key_1"] #PRIVATE KEY
    self.CLIENT_URL = key_json["face_api_endpoint"] #for HTTPSConnection
    
    #make connection to api
    self.conn = http.client.HTTPSConnection(self.CLIENT_URL)
    
    #standard header
    self.headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': KEY,
    }
    
    #timer lock on api transactions (limit: 20 per minute)
    self.start_time = time.time()
    self.transactions = 0
    
  def destruct(self):
    #saves data to file
    save_json_data = {}
    save_json_data[self.personGroupId] = {"persons":self.persons, "studentIds":self.studentIds,"faces":self.faces}
    save_data_path = os.path.join(os.getcwd(), "data.txt")
    outfile = open(save_data_path, "w")
    json.dump(save_json_data,outfile, indent = 4)
    outfile.close()
    #closes connection
    self.conn.close()
  
  """
  Request Types:
    1. create_personGroup -- def createPersonGroup(self, groupId = "", groupName = "")
    2. add_person -- def add_person(self, personName = "", studentId = "", studentEmail = "")
        #returns personId
    3. add_faces -- def add_faces(self, personId = "", face_urls = []):
    4. train -- def train(self):
    5. get_trainingStatus -- def get_trainingStatus(self):
    6. faceDetect -- def faceDetect(self, pic_url)
    7. faceIdentify -- def faceIdentify(self, faceIds = [], maxNumOfCandidates = 10, confidenceThreshold = 0.5 ):
  """

  #global request function for all transactions to prevent over-calling
  def makeRequest(self, method = "", endpoint = "", body = ""):
    # if(self.transactions % 5 == 0):
    #   print("{} transactions -- {}".format(self.transactions, endpoint))

    if(self.transactions > 18):
      time.sleep(60 - (time.time() - self.start_time))
      self.transactions = 0
      self.start_time = time.time()
      
    elif(abs(self.start_time - time.time()) > 60):
      self.transactions = 0
      self.start_time = time.time()
    
    #make request
    self.conn.request(method, endpoint, body, self.headers)

    #update transaction timer and count
    self.last_transaction = time.time()
    self.transactions += 1
    
  

  #######################
  # [createPersonGroup] #
  #######################
  def createPersonGroup(self, groupId = "", groupName = ""):
    
    try:
      
      #request data
      self.personGroupId = groupId
      params = urllib.parse.urlencode({"personGroupId" : self.personGroupId})
      body = '{"name": ' + groupName + ',"userData": ""}'

      #request
      self.makeRequest(method = "PUT", endpoint = "/face/v1.0/persongroups/{personGroupId}?%s" % params, body = body)
      response = self.conn.getresponse().read()

    except Exception as e:
      response = "[Errno {0}] {1}".format(e.strerror)
      print(response)
    
    #return request response
    return response
  
  
  ################
  # [add_person] #
  ################
  def add_person(self, personName = "", studentId = "", studentEmail = ""):
    
    try:
      
      #request data
      params = urllib.parse.urlencode({"personGroupId" : self.personGroupId})
      body = '{"name": "' + personName + '"}'

      #request
      self.makeRequest(method = "POST", endpoint = "/face/v1.0/persongroups/{personGroupId}/persons?%s" % params, body = body)
      
      #response
      response = json.loads(self.conn.getresponse().read())
      request_sucess = "personId" in response.keys()
      
      #initializing new student
      if(request_sucess):
        new_person_id = response["personId"]
        
        #check if student already exists in database before adding
        unique_person_id = (new_person_id not in self.persons.keys()) and (studentId not in self.studentIds.keys())
        if( unique_person_id ):
          self.persons[response["personId"]] = {"name":personName, "studentId":studentId, "email":studentEmail}
          self.studentIds[studentId] = new_person_id
          self.faces[personId] = []
        
        response = new_person_id
        
    except Exception as e:
      response = "[Errno {0}] {1}".format(e.errno, e.strerror)
      print(response)
     
    #return request response
    return response
  
  ###############
  # [add_faces] #
  ###############
  def add_faces(self, personId = "", face_urls = []):
    

    #request data
    params = urllib.parse.urlencode({"personGroupId" : self.personGroupId, 'personId':personId})
    
    self.faces[personId] += face_urls

    for face_url in face_urls:
      try:
        
        body = '{"url":"%s"}' % face_url
        
        #request
        self.makeRequest(method = "POST", endpoint = "/face/v1.0/persongroups/{personGroupId}/persons/{personId}/persistedFaces?%s" % params, body = body)
        response = json.loads(self.conn.getresponse().read())
        request_success = "persistedFaceId" in response.keys()

        if(request_success):
          #persistedFaceId of the added face, which is persisted and will not expire. 
          #Different from faceId which is created in Face - Detect and will expire in 24 hours after the detection call.
          persistedFaceId = response["persistedFaceId"]
          

      except Exception as e:
        response = "[Errno {0}] {1}".format(e.errno, e.strerror)
        print(response)
    
    #return request response
    return response

  #######################
  # [train_personGroup] #
  #######################
  def train(self):
    
    try:
      
      #request data
      params = urllib.parse.urlencode({"personGroupId" : self.personGroupId})

      #request
      self.makeRequest(method = "POST", endpoint = "/face/v1.0/persongroups/{personGroupId}/train?%s" % params, body = "{body}")
      response = self.conn.getresponse().read()
    except Exception as e:
      response = "[Errno {0}] {1}".format(e.errno, e.strerror)
      print(response)
    
    #return request response
    return response
  
  ########################
  # [get_trainingStatus] #
  ########################
  def get_trainingStatus(self):
    
    try:
      
      #request data
      params = urllib.parse.urlencode({"personGroupId" : self.personGroupId})

      #request
      self.makeRequest(method = "GET", endpoint = "/face/v1.0/persongroups/{personGroupId}/training?%s" % params, body = "{body}")
      response = json.loads(self.conn.getresponse().read())
      if("status" in response.keys()):
        status = response["status"]
        print("[{}] training for {}".format(status, self.personGroupId))
        response = status
    except Exception as e:
      response = "[Errno {0}] {1}".format(e.errno, e.strerror)
      print(response)
      response = ""
    
    #return request response
    return response
  
  ################
  # [faceDetect] #
  ################
  def faceDetect(self, pic_url):
    
    try:
      
      #request data
      params = urllib.parse.urlencode({
                    # Request parameters
                    'returnFaceId': 'true',
                    'returnFaceLandmarks': 'false',
                    'returnFaceAttributes': 'age,gender,smile',
                })
      
      body = '{ "url": "'+ pic_url +'" }'
      
      #request
      self.makeRequest(method = "POST", endpoint = "/face/v1.0/detect?%s" % params, body = body)
      response = json.loads(self.conn.getresponse().read())
      
      
      #finding the most likely face to detect (based on face bounding box)
      biggest_face_size = 0
      likely_face = None
      for face in response:
        face_size = face["faceRectangle"]["width"] * face["faceRectangle"]["height"]
        if( face_size > biggest_face_size ):
          biggest_face_size = face_size
          likely_face = face
          
      face_id = likely_face["faceId"]
      predicted_age = likely_face["faceAttributes"]["age"]
      predicted_gender = likely_face["faceAttributes"]["gender"]
      predicted_smile = likely_face["faceAttributes"]["smile"]
      print("AGE: {}, GENDER: {}, SMILE: {}".format(predicted_age, predicted_gender, predicted_smile))
      response = face_id
      
    except Exception as e:
      response = "[Errno {0}]".format( e)
      print(response)
      response = ""
    
    #return request response
    return response
  
  ##################
  # [faceIdentify] #
  ##################
  def faceIdentify(self, faceIds = [], maxNumOfCandidates = 10, confidenceThreshold = 0.5 ):
    
    try:
      
      #request data
      params = urllib.parse.urlencode({})
      body = { "personGroupId": self.personGroupId, "faceIds":faceIds, "maxNumOfCandidatesReturned": maxNumOfCandidates, "confidenceThreshold": confidenceThreshold }
      
      #request
      self.makeRequest(method ="POST", endpoint = "/face/v1.0/identify?%s" % params,  body = json.dumps(body))
      response = json.loads(self.conn.getresponse().read())
      if(response is None):
        return ""
      candidates = response[0]["candidates"]
      if(len(candidates) > 1):
        rankedCandidates = sorted(candidates, key=lambda x: x["confidence"], reverse=True)[0]
        likely_personId = rankedCandidates["personId"]
        confidence = rankedCandidates["confidence"]
        response = likely_personId
        print(self.persons[likely_personId], confidence)
        
      elif(len(candidates) == 1):
        likely_personId = candidates[0]["personId"]
        confidence = candidates[0]["confidence"]
        response = likely_personId
        print(self.persons[likely_personId], confidence)
        
      else:
        response = "No candidates"
        response = ""
      #take response and log in student_id with timestamp
    except Exception as e:
      response = "[Errno ] {}".format(e)
      response = ""
      print(response)
    
    #return request response
    return response