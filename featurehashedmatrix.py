import re
import reader

class FeatureHashedMatrix:

  def __init__(self,buckets):
    self.buckets = buckets
    self.matrix = []
    self.categories = [] #TODO: huge memory hog

  def featurehash(self,features):
    ret = [0]*self.buckets
    for feature in features:
      h = hash(feature) % self.buckets
      ret[h] += 1
    return ret

  def addrow(self,text):
    text = self.clean(text)
    words = re.split('[\s]',text)#split words on whitespaces
    # words = re.split('[\W]',text)#split words on not alphanumeric
    row = self.featurehash(words)
    self.matrix.append(row)
    self.categories.append(reader.extractCategories(text))

  def clean(self,text):
    return re.sub(r"\{\{.*?\}\}", '', text)