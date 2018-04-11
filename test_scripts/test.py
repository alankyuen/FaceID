import os,json
# saved_data = {}
# infile = open(os.path.join(os.getcwd(),"students2.txt"),"r")
# saved_data = json.load(infile)

# infile.close()
# infile = open(os.path.join(os.getcwd(),"students.txt"),"r")
# loaded = json.load(infile)
# loaded[list(saved_data.keys())[0]] = saved_data[list(saved_data.keys())[0]]

with open(os.path.join(os.getcwd(),"students.txt"),"r") as outfile:
	print(json.load(outfile))