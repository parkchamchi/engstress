import os
import json

class CMUDict():
	"""
	Fetch the pronunciation dictionary from the text file (about 3.7MiB)
	"""

	def __init__(self, txtfilename="dicts/cmudict-0.7b", jsonfilename="dicts/cmudict.json"):
		self.txtfilename = txtfilename
		self.jsonfilename = jsonfilename

		#If there already is JSON file created
		if os.path.exists(jsonfilename):
			with open(jsonfilename, "rt") as fin:
				self.dict = json.load(fin)

		#Else, create one
		else:
			self.dict = {}

			#Read the text file
			#Reading as a text file throws an UnicodeDecodeError since the file has an illegal squence b'D\xc9J\xc0'
			with open(txtfilename, "rb") as fin:
				for line in fin.read().split(b"\r\n"):
					if not line or line.startswith(b";;;"):
						#skip comments
						continue
					
					"""
					Formatted as:
						RESPLENDENT  R IY0 S P L EH1 N D AH0 N T
						RESPOND  R IH0 S P AA1 N D
						RESPOND(1)  R IY0 S P AA1 N D
					"""

					word, _, pronun = line.partition(b'  ')


					#to str
					try:
						word = word.decode("ascii")
						pronun = pronun.decode("ascii")
					except:
						continue

					self.dict[word] = pronun

			#dump as JSON
			with open(jsonfilename, "wt", encoding="ascii") as fout:
				json.dump(self.dict, fout, indent='\t')

	def get(self, word):
		word = word.upper()

		if word not in self.dict:
			return None

		return self.dict[word]

if __name__ == "__main__":
	cmu = CMUDict()
	res = cmu.get("car")
	print(res)