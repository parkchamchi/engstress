import os
import json
import csv
import string
import copy

class CMUDict():
	"""
	Fetch the pronunciation dictionary from the text file (about 3.7MiB)
	"""

	def __init__(self, ignore_mono=True, ignore_dupls=True, txtfilename="dicts/cmudict.dict", jsonfilename="dicts/cmudict.json"):
		"""
		:param ignore_mono: ignore monosyllable words (is, it, for, ...)
		:param ignore_dupls: ignore all words that has several pronunciations that differ in stress
		"""

		#self.stress1 = 'ˈ'
		#self.stress2 = 'ˌ'

		self.acute = '\u0301'
		self.grave = '\u0300'

		self.ignore_dupls = ignore_dupls
		self.ignore_mono = ignore_mono

		self.txtfilename = txtfilename
		self.jsonfilename = jsonfilename
		
		#Load symbols
		self.symbols = {}
		with open("symbols.csv", "rt", newline='', encoding="utf-8") as fin:
			cin = csv.DictReader(fin)
			for row in cin:
				self.symbols[row["symbol"]] = row
				del row["symbol"]

		#If there already is JSON file created
		if os.path.exists(jsonfilename):
			with open(jsonfilename, "rt") as fin:
				self.dict = json.load(fin)

		#Else, create one
		else:
			self.dict = {}

			#Read the text file
			try:
				with open(txtfilename, "rt") as fin:
					for line in fin:
						if line.endswith('\n'):
							line = line[:-1]

						#skip comments
						if not line or line.startswith(";;;"):
							continue

						"""
						Formatted as:
							reslendent  R IY0 S P L EH1 N D AH0 N T
							respond  R IH0 S P AA1 N D
							respond(2)  R IY0 S P AA1 N D #comment
						"""	

						word, _, pronun = line.partition(' ')
						word = word.lower() #no effect
						if '#' in pronun:
							pronun = pronun.split('#')[0]
							pronun = pronun.strip()

						self.dict[word] = pronun

			except UnicodeDecodeError:
				#Reading cmudict-0.7b as a text file throws an UnicodeDecodeError since the file has an illegal squence b'D\xc9J\xc0'
				with open(txtfilename, "rb") as fin:
					for line in fin.read().split(b"\r\n"):
						if not line or line.startswith(b";;;"):
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
							word = word.decode("ascii").lower()
							pronun = pronun.decode("ascii")
						except:
							continue

						self.dict[word] = pronun

			#dump as JSON
			with open(jsonfilename, "wt", encoding="ascii") as fout:
				json.dump(self.dict, fout, indent='\t')

	def getPronun(self, word):
		word = word.lower()

		if word not in self.dict:
			return ""

		pronun = self.dict[word]
		_, shape = self.getClusters(pronun)

		if self.ignore_mono and self.isMono(shape):
			return ""

		if self.ignore_dupls and self.hasDupl(word, shape):
			return ""

		return pronun

	def getClusters(self, pronun):
		"""
		cluster
			['K L', 'AH1', 'S T', 'ER0'], 'C1CV'
		idle
			['', 'AY1', 'D', 'AH0', 'L'], 'C1C0C'
		naive
			['N', 'AY2', 'IY1', 'V'], 'C21C'
		"""

		if not pronun:
			return None

		clusters = []
		cluster = []
		prev = 'C' #what the cluster is holding
		#isInitial = True
		shape = "" #CVCVC...

		for symbol in pronun.split():
			#Check if the symbol is a consonant or a vowel
			current = self.symbols[symbol]["value"]
			
			if prev == 'C' and prev == current:
				#constant cluster
				cluster.append(symbol)
			else:
				#Change the cluster
				clusters.append(' '.join(cluster))
				shape += prev if prev == 'C' else self.symbols[cluster[0]]["stress"]
				cluster = [symbol]

			prev = current

		#Last one
		clusters.append(' '.join(cluster))
		shape += prev if prev == 'C' else self.symbols[cluster[0]]["stress"]

		return clusters, shape

	def hasDupl(self, word, shape):
		"""
		Check if the word has different pronunciation that differ in stress
		e.g. record (noun: C1C0C) (verb: C0C1C)
		The first entry can be "word(1)" or "word(2)" by the version of cmudict.
		
		:param word: This is assumed to be exist in the self.dict
		"""
		#Get the original shape

		i = 1
		while True:
			entry = "{}({})".format(word, i)
			if entry not in self.dict:
				if i == 1:
					i += 1
					continue #Try (2)
				else: #No more entries
					return False 

			entry_pronun = self.dict[entry]
			_, entry_shape = self.getClusters(entry_pronun)

			if shape != entry_shape: #Found a duplicate
				return True 

			i += 1

	def isMono(self, shape):
		if shape in ["C0", "C1", "C0C", "C1C"]:
			return True

	def getIPA(self, word):
		pronun = self.getPronun(word)

		if not pronun: #return the original
			return word

		ipa = ""
		
		for symbol in pronun.split():
			symbol = self.symbols[symbol]
			ipa += symbol["ipa"]
			if symbol["stress"] == '1':
				ipa += self.acute
			elif symbol["stress"] == '2':
				ipa += self.grave

		return ipa

	def setStress(self, word):
		pass

if __name__ == "__main__":
	cmu = CMUDict()
		
	for word in cmu.dict:
		pronun = cmu.getPronun(word)