import xml.etree.ElementTree as etree
import html, re, sys

def parseXML(filename, textCallback, count=5):
  i=0
  with open(filename) as xml:
    for event, elem in etree.iterparse(xml, events=('end', )):
      if elem.tag == "{http://www.mediawiki.org/xml/export-0.10/}text":
        if elem.text.startswith("#REDIRECT"):
          continue
        textCallback(elem.text)
        i+=1
        if i >= count:
          break;
      else:
        elem.clear()

def callback(text):
  text = html.unescape(text)
  categories = extractCategories(text)
  #print(categories)
  findCleanupTag(text)

def extractCategories(text):
  return re.findall(r"\[\[Category:([^\]]+)\]\]", text)

def findCleanupTag(text):
  match = re.search("{{buzzword[^}]*}}", text)
  if match:
    print(match)
    #print(text[:200])


if __name__ == "__main__":
  if len(sys.argv) > 1:
    count = int(sys.argv[1])
  else:
    count = 5
  parseXML("enwiki-20161101-pages-articles-multistream.xml", callback, count)
