import xml.etree.ElementTree as etree
import html, re, sys
import pickle
from collections import Counter

CONTEXT=5000

TAGS=["buzzword", "abbreviations", "manual", "repetition", "too many see alsos", "overlinked", "overcoloured", "technical", "peacock", "Overcite", "dead end"]
CATEGORIES=set(['Living people', 'American male film actors', 'American films', 'Spanish-language films', 'Windows games', 'English-language albums', 'Quantum mechanics', 'Flowers', 'American artists', 'French films'])
POSITIVES = {}
PROCESSED = 0
categoryCounter = Counter()

def parseXML(filename, callbacks, count=5):
  global PROCESSED
  i=0
  with open(filename) as xml:
    for event, elem in etree.iterparse(xml, events=('end', )):
      if elem.tag == "{http://www.mediawiki.org/xml/export-0.10/}text":
        if elem.text is None or elem.text.startswith("#REDIRECT"):
          continue
        if i >= PROCESSED:
          for callback in callbacks:
            callback(elem.text, i)
          PROCESSED += 1
        i+=1
        elem.clear()
        if i >= count:
          break;
      else:
        elem.clear()

def callback(text, index):
  if index % 1000 == 0:
    print(".", end="")
    sys.stdout.flush()
  text = html.unescape(text)
  extractCategories(text)
  extractTags(text)

def extractTags(text):
  for tag in TAGS:
    context = findCleanupTag(text, tag)
    if context:
      insertPositive(tag, context)
      print("%s!" % tag)

def extractCategories(text):
  categories = re.findall(r"\[\[Category:([^\]]+)\]\]", text)
  categoryCounter.update(categories)
  for c in categories:
    if c in CATEGORIES:
      insertPositive(c, text)

def cleanStraglers(text):
  start = end = None
  match = re.search("^\w*", text, flags=re.DOTALL)
  if match:
    start = match.span()[1]
  match = re.search("\w*$", text, flags=re.DOTALL)
  if match:
    end = match.span()[0]
  return text[start:end]


def findCleanupTag(text, tag):
  match = re.search(r"{{%s[^}]*}}"%tag, text, flags=re.DOTALL)
  if match:
    start, end = match.span()
    cstart = cend = None
    if start >= CONTEXT:
      cstart = start - CONTEXT
    if len(text)-end >= CONTEXT:
      cend = end+CONTEXT
    context = text[cstart:start]+" "+text[end:cend]
    return cleanStraglers(context)

def insertPositive(tag, context):
  a = POSITIVES.get(tag)
  if a is None:
    a = []
    POSITIVES[tag] = a
  a.append(context)

PICKLE_FILE="data.pickle"

def store():
  with open(PICKLE_FILE, "wb") as f:
    pickle.dump((PROCESSED, POSITIVES, categoryCounter), f, pickle.HIGHEST_PROTOCOL)

def load():
  global PROCESSED, POSITIVES, categoryCounter
  try:
    with open(PICKLE_FILE, "rb") as f:
      (PROCESSED, POSITIVES, categoryCounter) = pickle.load(f)
  except:
    pass

def displayStats():
  print("%i Articles processed:" % PROCESSED)
  for tag in TAGS:
    print("%s has %i positives" % (tag, len(POSITIVES.get(tag, []))))
  print("Most Common categories:")
  for c, count in categoryCounter.most_common(5000):
    print(c, "(%i)"%count)


if __name__ == "__main__":
  if len(sys.argv) > 1:
    count = int(sys.argv[1])
  else:
    count = 5
  load()
  displayStats()
  parseXML("enwiki-20161101-pages-articles-multistream.xml", [callback], count)
  store()
