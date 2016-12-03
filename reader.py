import xml.etree.ElementTree as etree
import html, re, sys
import pickle
from collections import Counter
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from featurehashedmatrix import FeatureHashedMatrix

CONTEXT=5000

TAGS=["buzzword", "abbreviations", "manual", "repetition", "too many see alsos", "overlinked", "overcoloured", "technical", "peacock", "Overcite", "dead end"]
CATEGORIES=set(['Living people', 'American male film actors', 'American films', 'Spanish-language films', 'Windows games', 'English-language albums', 'Quantum mechanics', 'Flowers', 'American artists', 'French films'])
POSITIVES = {}
PROCESSED = 0
categoryCounter = Counter()
CATEGORY_LABELS = []
CATEGORY_LABEL_MAP = {}
CATEGORY_MATRIX = []
kmeans = None

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
  return categories

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

def insertPositive(key, entry, dataDict=POSITIVES, default=None, addFunc='append'):
  if default is None:
    default = []
  a = dataDict.get(key)
  if a is None:
    a = default
    dataDict[key] = a
  a.__getattribute__(addFunc)(entry)

def displayStats():
  print("========= %i Articles processed: =========" % PROCESSED)
  for tag in TAGS:
    print("%s has %i positives" % (tag, len(POSITIVES.get(tag, []))))
  print()
  print("========= Most Common categories: =========")
  for c, count in categoryCounter.most_common(10):
    print(c, "(%i)"%count)

def createCategoryMatrix(buckets=100):
  global CATEGORY_LABELS, CATEGORY_MATRIX, CATEGORY_LABEL_MAP
  fh = FeatureHashedMatrix(buckets)
  for label, category in enumerate(CATEGORIES):
    CATEGORY_LABEL_MAP[label] = category
    articles = POSITIVES.get(category)
    for article in articles:
      fh.addrow(article)
      CATEGORY_LABELS.append(label)
  CATEGORY_MATRIX = fh.matrix

def runKmeans():
  global kmeans
  kmeans = KMeans(n_clusters=len(CATEGORIES), n_jobs=-1).fit(CATEGORY_MATRIX)

def evaluateKmeans():
  clusters = {}
  print(len(kmeans.labels_), len(CATEGORY_LABELS))
  for klabel, clabel in zip(kmeans.predict(CATEGORY_MATRIX), CATEGORY_LABELS):
    insertPositive(klabel, [clabel],
        dataDict=clusters, default=Counter(), addFunc='update')
  for klabel, counter in clusters.items():
    print("Cluster (%i)" % klabel)
    for l, count in counter.most_common():
      category = CATEGORY_LABEL_MAP[l]
      count_category = len(POSITIVES.get(category))
      print("label (%s)" %category, "(%f)"%(count/count_category))

PICKLE_FILE="data.pickle"

def store():
  with open(PICKLE_FILE, "wb") as f:
    pickle.dump(
        (PROCESSED, POSITIVES, categoryCounter, CATEGORY_LABELS, CATEGORY_MATRIX, kmeans, CATEGORY_LABEL_MAP), f, pickle.HIGHEST_PROTOCOL)

def load():
  global PROCESSED, POSITIVES, categoryCounter, CATEGORY_LABELS, CATEGORY_MATRIX, kmeans, CATEGORY_LABEL_MAP
  try:
    with open(PICKLE_FILE, "rb") as f:
      (PROCESSED, POSITIVES, categoryCounter, CATEGORY_LABELS, CATEGORY_MATRIX, kmeans, CATEGORY_LABEL_MAP) = pickle.load(f)
  except IOError as e:
    print(e)

if __name__ == "__main__":
  if len(sys.argv) > 1:
    count = int(sys.argv[1])
  else:
    count = 5
  load()
  parseXML("enwiki-20161101-pages-articles-multistream.xml", [callback], count)
  createCategoryMatrix()
  runKmeans()
  store()
  displayStats()
  evaluateKmeans()
