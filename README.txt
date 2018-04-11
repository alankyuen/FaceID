Installation:

	1. 	Virtualenv

	2.	#python sdk for azure blob storage
		!pip install azure-storage-blob
		!pip install azure-storage-file
		!pip install azure-storage-queue

	3.	update "azure_service_keys.txt" with your own keys

	4.	init.py if you need to create new personGroup

	5. 	auto_reg.py to register one person at a time (LIVE) or manual_reg.py if you have a bunch of profile data

	6.	once you've registered new people, run train.py

	7.	run run.py when you want to use face_id