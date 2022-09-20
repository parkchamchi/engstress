# Engstress: English Stress Indicator
This script indicates the stresses of english words.<br>
Try the [HTML/Javascript version](https://parkchamchi.github.io/engstress/)!<br>
<br>

# Example

### Importing

```python
from engstress import engstress

es = engstress.Engstress()
print(es.process("indicate"))
```
`> índicate`

<br>

### Handles inflections.
```python
print(es.process("diagram diagrams distinguish distinguishing thirsty thirstiest"))
```
`> díagram díagrams distínguish distínguishing thírsty thírstiest`

<br>

### For some words whose pronunciations differ by their parts-of-speech, NLTK can be used.
```python
es.load_nltk() # es = engstress.Engstress(use_nltk=True) loads nltk on construction.
print(es.process_nltk("I present you this present."))
```
`Loading NLTK...`<br>
`Loaded NLTK.`<br>
`I presént you this présent.`<br>
<br>
This may lose some structural details of the input.

<br>

### "Stress" entry on Webster's Dictionary, 1913
```
STRESS
Stress, n. Étym: [Abbrev. fr. distréss; or cf. OF. estrecier to
press, pinch, (assúmed) LL. strictiare, fr. L. strictus. See
Distréss.]

1. Distréss. [Obs.] Sad hérsal of his héavy stress. Spenser.

2. Préssure, strain; — used chíefly of ímmatérial things;
excépt in mechánics; hence, úrgency; impórtance; weight; signíficance.
The fáculties of the mind are impróved by éxercise,
yet they must not be put to a stress beyónd their strength. Locke.
A bódy may as well lay too líttle as too much stress upón a dream. L'Estránge.

3. (Mech. & Phýsics)

Defn: The force, or combinátion of forces, which produces a strain;
force exérted in ány diréction or mánner betwéen contíguous bódies, or parts of bódies,
and táking specífic names accórding to its diréction, or mode of áction,
as thrust or préssure, pull or ténsion, shear or tangéntial stress. Rankine.
Stress is the mútual áction betwéen pórtions of mátter. Clerk Maxwell.

4. (Pron.)

Defn: Force of útterance expénded upón words or sýllables.
Stress is in Énglish the chief élement in accent and is one of the most impórtant in émphasis.
See Guide to pronunciátion, §§ 31-35.

5. (Scots Law)

Defn: Distréss; the act of distráining; álso, the thing distráined.
Stress of voice, unúsual exértion of the voice.
— Stress of wéather, constráint impósed by contínued bad wéather;
as, to be dríven back to port by stress of wéather.
— To lay stress upón, to attách great impórtance to; to émphasize.
"Consíder how great a stress is laid upón this dúty." Atterbury.
— To put stress upón, or To put to a stress, to strain.

STRESS
Stress, v. t.

1. To press; to urge; to distréss; to put to dífficulties. [R.] Spenser.

2. To subjéct to stress, préssure, or strain.
```

<br>

## License
The [dictionary JSON file](webster.json) is processed (by `Engstress.__init__()`) from [Webster's Dictionary, 1913](https://www.gutenberg.org/ebooks/29765) ([HTML file, which was used](https://www.gutenberg.org/cache/epub/29765/pg29765.html)), provided by Project Gutenberg.
While it is in the public domain, please check [Project Gutenberg License](https://www.gutenberg.org/policy/license.html).<br>
The rest is of MIT License.