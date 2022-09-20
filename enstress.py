import os
import json
import itertools

class Engstress():
	"""
	Reads 1913 Webster's Dictionary, as in
		https://www.gutenberg.org/cache/epub/29765/pg29765.html
	"""

	def __init__(self, no_secondary=False, use_nltk=False, jsonpath="webster.json", htmlpath="dicts/pg29765.htm"):
		"""
		:param no_secondary: do not indicate the secondary stresses
		:param use_nltk: use the NLTK library to process words whose pronunciation differs by it PoS. (e.g. record)
		:param htmlpath: only used when jsonpath doesn't exist
		"""

		self.no_secondary = no_secondary

		if use_nltk:
			self.load_nltk() #This sets self.use_nltk
		else:
			self.use_nltk = False

		self.jsonpath = jsonpath
		self.html = htmlpath

		self.acute = '\u0301' #primary
		self.grave = '\u0300' #secondary

		if os.path.exists(jsonpath):
			#Read the processed JSON file
			with open(jsonpath, "rt") as fin:
				self.dict = json.load(fin)

		else:
			self.dict = {}

			#Load intermediary JSON, as bs4 for this HTML is slow (Espicially "html-parser")
			inter_jsonpath = htmlpath + ".json"
			if os.path.exists(inter_jsonpath):
				with open(inter_jsonpath, "rt", encoding="utf-8") as fin:
					entries = json.load(fin)

			else:
				from bs4 import BeautifulSoup as Soup

				entries = []

				#Read the HTML
				with open(htmlpath, "rt", encoding="utf-8") as fin:
					html = fin.read()
				soup = Soup(html, "lxml")

				for p in soup.find_all("p"):
					for br in p.find_all("br"):
						br.replace_with('\n')

					text = p.get_text()

					#"1.", "(a)" ...
					if not text[0].isupper(): 
						continue
					
					#Ignore single-letter entries
					if len(text) < 2:
						continue

					#Defn, Note, Syn, End of, Title, ...
					if not text[1].isupper(): 
						continue

					if "Etym:" in text:
						text = text.split("Etym:")[0]

					"""
					ACETONAEMIA; ACETONEMIA
					Ac`e*to*næ"mi*a, Ac`e*to*ne"mi*a, n. [NL. See Acetone; Hæma-.] (Med.)
					"""

					word_line, rest_line = [e for e in text.split('\n') if e][:2]
					entries.append([word_line, rest_line])

				#Dump intermediary JSON
				with open(inter_jsonpath, "wt", encoding="utf-8") as fout:
					json.dump(entries, fout, indent='\t')

			for word_line, rest_line in entries:
				words = []
				prons = []
				pos = []
				valid_pos = ["n.", "a.", "v.t.", "v.i.", "adv.", "p.p.", "prep.", "v.", "p.", "t.", "i.", "pret.", "imp.", "pl.", "obs.", "conj.", "interj.", "pron."]
				meaningful_pos = ["n.", "v.", "a.", "adv."]

				#Take out the words first
				#Check if the words are valid (i.e. only of letters)
				words = word_line.split('; ')
				valid_words = True
				
				for word in words:
					if any([not (e.isalpha()) for e in word]):
						valid_words = False
						break
				if not valid_words:
					continue

				#Take out the pronunciations
				tokens = rest_line.split()

				for token in tokens.copy():
					if any(map(token.startswith, valid_pos)):
						break

					if token.startswith('(') or any(map(token.endswith, [')', '),'])) or token == "or":
						tokens.pop(0)
						continue

					for c in [',', '.', ';']:
						if token.endswith(c):
							token = token[:-1]

					#Handle 'ae' diagraph
					token = token.replace('æ', 'ae').replace('Æ', 'Ae')
					#Handle typo - double stress mark
					token = token.replace('""', '"').replace('"`', '`').replace('*"', '"').replace('*`', '`')

					prons.append(token)
					tokens.pop(0)

				#Take out the POS
				for token in tokens.copy():
					if token in ["L.", "E."]:
						break

					if token[0].isalpha() and any(map(token.endswith, [".", ".;"])):
						if token.endswith(';'):
							token = token[:-1]

						if token not in valid_pos:
							continue

						pos.append(token)
						tokens.pop(0)
					else:
						break
					
				#Normalize
				if pos != [] and pos[-1] == "pl.":
					pos.pop()
				
				if 'v.t.' in pos: #appears to be a type of 'v. t.'
					pos.remove('v.t.')
					pos.extend(['v.', 't.'])

				pos = [e for e in pos if e in meaningful_pos]

				#Put to the dict
				"""
				{
					word1: {
						pron1: pos1
					}
					word2: {
						pron2: pos2
						pron2': pos2'
					}
				}
				"""

				for word in words:
					pron_for_word = self.match(word, prons)
					if not pron_for_word: #no matching pron
						continue

					if word not in self.dict:
						self.dict[word] = {pron_for_word: pos}
					else:
						#The word already exists in dict
						#Check if the pron already exists
						if pron_for_word in self.dict[word]:
							#It it does, merge
							self.dict[word][pron_for_word] = list(set(self.dict[word][pron_for_word]) | set(pos))
						else:
							#Otherwise, create a new one
							self.dict[word][pron_for_word] = pos

			#Reiterate
			for word, dic in self.dict.items():
				if len(dic) == 1:
					continue

				# CONTENT {'Con*tent': ['a.'], 'Con"tent': ['n.'], 'Con*tent"': ['n.', 't.', 'v.']}
				shapes = {pron: self.shape(pron) for pron in dic}

				for i in range(8):
					to_dels = []
					
					if i == 0:
						#Check if one of pron is unstressed (shape: 0...0)
						for pron in dic:
							if int(shapes[pron]) == 0:
								to_dels.append(pron)

					elif i == 1:
						#Check: just different stress location (Tee"ny - Teen"y)
						for pron1, pron2 in itertools.combinations(dic, 2):
							if shapes[pron1] == shapes[pron2]:
								to_dels = [pron2]
								break

					elif i == 2:
						#Check: Non"plus - 'Non"plus`
						for pron1, pron2 in itertools.permutations(dic, 2):
							if shapes[pron1] == shapes[pron2].replace('1', '0'):
								to_dels = [pron2]
								break

					elif i == 3:
						#Check: Pol`y*pode' - 'Pol"y*pode:
						for pron1, pron2 in itertools.permutations(dic, 2):
							if shapes[pron1] == shapes[pron2].replace('1', '2'):
								to_dels = [pron2]

					elif i == 4:
						#Check: A*ca"ci*a' - 'A*ca"cia' ['0200', '020']
						for pron1, pron2 in itertools.permutations(dic, 2):
							if shapes[pron1] == shapes[pron2][:-1]:
								to_dels = [pron2]

					elif i == 5:
						#Check: 2 primary stresses (ATTEST)
						for pron in dic:
							if shapes[pron].count('2') >= 2:
								to_dels = [pron]

					elif i == 6:
						#Check if they have same POS (BISMER)
						for pron1, pron2 in itertools.combinations(dic, 2):
							if dic[pron1] == dic[pron2]:
								to_dels = [pron2]
								break

					elif i == 7:
						#Check one of them has empty POS (PROGRESS)
						for pron in dic:
							if dic[pron] == []:
								to_dels = [pron]
								break

					for to_del in to_dels:
						del dic[to_del]

					if len(dic) == 1:
						break

			#The remaining pairs differ by their POS
			#Reiterate
			"""
			Final JSON:
			{
				WORD1: PRON1,
				WORD2: {
					PRON2: [...]
					PRON3: [...]
				}
			}
			"""
			for word, dic in self.dict.items():
				if len(dic) == 1:
					self.dict[word] = self.indicateStress(list(dic.keys())[0])
				else:
					for pron in list(dic.keys()):
						pron_stress = self.indicateStress(pron)
						self.dict[word][pron_stress] = dic[pron]
						del self.dict[word][pron]
			
			#Dump JSON
			with open(jsonpath, "wt", encoding="utf-8") as fout:
				json.dump(self.dict, fout, indent='\t')
		
	def load_nltk(self):
		print("Loading NLTK...")
	
		try:
			from nltk.tag import pos_tag
			from nltk.tokenize import sent_tokenize, word_tokenize
			from nltk.tokenize.treebank import TreebankWordDetokenizer

			self.pos_tag = pos_tag
			self.sent_tokenize = sent_tokenize
			self.word_tokenize = word_tokenize
			self.detokenize = TreebankWordDetokenizer().detokenize

			self.use_nltk = True
			print("Loaded NLTK.")

		except Exception as exc:
			print("ERROR: Failed to import NLTK.")
			self.use_nltk = False

	def match(self, word, prons):
		"""
		Check if the pronunciation ('The*or"ic') matches the word ('THEROIC')
		& return the right one
		"""
		
		for pron in prons:
			normalized = ''.join([c if c.isalpha() else '' for c in pron]).upper()
			if normalized == word:
				return pron
		return False

	def shape(self, pron):
		"""
		'Guar"an*tee`' -> "201"
		"""

		shape = ""
		for c in pron:
			if c == '"':
				shape += '2' #primary
			elif c == '`':
				shape += '1' #secondary
			elif c == '*':
				shape += '0' #no stress
		
		#Check the last
		if pron[-1] not in ['"', '`', '*']:
			shape += '0'

		return shape
	
	def indicateStressOnCluster(self, cluster, c):
		"""
		on" -> ón
		Assumes cluster to be .lower()'ed
		"""

		if c == '*':
			return cluster
		elif c == '"':
			c = self.acute
		elif c == '`':
			c = self.grave

		vowels = ['a', 'e', 'i', 'o', 'u']
		vowel_loc = len(cluster)-1
		for vowel in vowels:
			if vowel in cluster:
				vowel_loc = min(vowel_loc, cluster.index(vowel))

		if cluster[vowel_loc] not in vowels and 'y' in cluster:
			vowel_loc = cluster.index('y')

		cluster = cluster[:vowel_loc+1] + c + cluster[vowel_loc+1:]

		return cluster
		
	def indicateStress(self, pron):
		out = ""
		cluster = ""

		for c in pron.lower():
			if c in ['"', '`', '*']:
				out += self.indicateStressOnCluster(cluster, c)
				cluster = ""
			else:
				cluster += c
		if cluster:
			out += cluster

		return out

	#Below: used after self.dict is created

	def getPron(self, word):
		return self.dict.get(word.upper())

	def getStress(self, word, pos=None):
		"""
		:param pos: NLTK PoS tag. (optional)
		"""

		infl_from = infl_to = None

		pron = self.getPron(word)
		if not pron:
			"""
			Handle inflections
			-s (words), -es (dishes) -ies -> -y (skies)
			-ing (making)
			-ed -> -e (baked) -> x (looked)
			-er, -est (bigger)
			"""

			inflections = [("s", ""), ("es", ""), ("ies", "y"), ("ing", ""), ("ed", "e"), ("ed", ""), ("er", ""), ("est", ""), ("er", "e"), ("est", "e"), ("ier", "y"), ("iest", "y")]
			for infl_from, infl_to in inflections:
				if word.endswith(infl_from):
					pron = self.getPron(word[:-len(infl_from)] + infl_to)
					if pron:
						break

			if not pron:			
				return word

		#Handle words with several pronunciations
		if type(pron) is not str:
			if not pos:
				return word

			nltk_pos = {
				"N": "n.",
				"V": "v.",
				"J": "a.",
				"R": "adv."
			}
			pos = pos[0]
			if pos not in nltk_pos:
				return word

			pos = nltk_pos[pos]

			for subpron, subpos in pron.items():
				if pos in subpos:
					pron = subpron
					break

			if type(pron) is not str:
				return word

		if self.no_secondary:
			if self.grave in pron:
				pron = pron.replace(self.grave, '')

		#Restore
		if infl_from or infl_to:
			if not infl_to:
				pron += infl_from
			else:
				#infl_to can be either 'e' of 'y' (for now)
				if infl_to == 'e':
					#e -> ed
					pron += infl_from[1:]
				else:
					#y -> ies
					if any(map(pron.endswith, [self.acute, self.grave])):
						#Rare case where the last 'y' is stressed
						y_stress = pron[-1]
						pron = pron[:-2] + "i" + y_stress + infl_from[1:]

					else:
						pron = pron[:-1] + infl_from

		#Correct cases
		j = 0
		for c in word:
			if c.islower():
				continue

			if pron[j] in [self.acute, self.grave]:
				j += 1

			pron = pron[0:j] + c.upper() + pron[j+1:]

			j += 1

		return pron

	def process(self, corpus):
		"""
		This char-by-char version will save minor details of the corpus.
		"""
		#.split(' ') version? regex?

		word = ""
		out = ""

		for c in corpus:
			if c.isalpha():
				word += c
			else:
				if word:
					out += self.getStress(word)
					word = ""
				out += c
		if word:
			out += self.getStress(word)

		return out

	def process_nltk(self, corpus):
		"""
		Replace '\n' with something else before tokenizing.
		"""

		if not self.use_nltk:
			print("ERROR: NLTK is not loaded!")
			return self.process(corpus)

		out = []
		newline = " 😺😸😺\n"
		corpus = corpus.replace('\n', newline)

		for sent in self.sent_tokenize(corpus):
			tokens = self.pos_tag(self.word_tokenize(sent))

			#Modify the tokens
			for i in range(len(tokens)):
				token, pos = tokens[i]
				if token.isalpha():
					tokens[i] = self.getStress(token, pos)
				else:
					tokens[i] = token
			
			out.append(self.detokenize(tokens).replace(newline.strip(), '\n'))

		return ' '.join(out)

		
######################################################
if __name__ == "__main__":

	corpus = """
	STRESS
	Stress, n. Etym: [Abbrev. fr. distress; or cf. OF. estrecier to
	press, pinch, (assumed) LL. strictiare, fr. L. strictus. See
	Distress.]

	1. Distress. [Obs.] Sad hersal of his heavy stress. Spenser.

	2. Pressure, strain; — used chiefly of immaterial things; 
	except in mechanics; hence, urgency; importance; weight; significance. 
	The faculties of the mind are improved by exercise, 
	yet they must not be put to a stress beyond their strength. Locke. 
	A body may as well lay too little as too much stress upon a dream. L'Estrange.

	3. (Mech. & Physics)

	Defn: The force, or combination of forces, which produces a strain; 
	force exerted in any direction or manner between contiguous bodies, or parts of bodies, 
	and taking specific names according to its direction, or mode of action, 
	as thrust or pressure, pull or tension, shear or tangential stress. Rankine. 
	Stress is the mutual action between portions of matter. Clerk Maxwell.

	4. (Pron.)

	Defn: Force of utterance expended upon words or syllables. 
	Stress is in English the chief element in accent and is one of the most important in emphasis. 
	See Guide to pronunciation, §§ 31-35.

	5. (Scots Law)

	Defn: Distress; the act of distraining; also, the thing distrained.
	Stress of voice, unusual exertion of the voice.
	— Stress of weather, constraint imposed by continued bad weather;
	as, to be driven back to port by stress of weather.
	— To lay stress upon, to attach great importance to; to emphasize.
	"Consider how great a stress is laid upon this duty." Atterbury.
	— To put stress upon, or To put to a stress, to strain.

	STRESS
	Stress, v. t.

	1. To press; to urge; to distress; to put to difficulties. [R.] Spenser.

	2. To subject to stress, pressure, or strain.
	"""

	engstress = Engstress(no_secondary=True)

	print(engstress.process(corpus))