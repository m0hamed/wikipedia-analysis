import re

class FeatureHashedMatrix:

  def __init__(self,buckets):
    self.buckets = buckets
    self.matrix = []

  def featurehash(self,features):
    ret = [0]*self.buckets
    for feature in features:
      h = hash(feature) % self.buckets
      ret[h] += 1
    return ret

  def addrow(self,text):
    print(text)
    text = self.clean(text)
    print(text)
    words = re.split('[\s]',text)
    row = self.featurehash(words)
    self.matrix.append(row)

  def clean(self,text):
    #re.sub(r'\{\{(.*?)\}\}', ' ', text)
    return text