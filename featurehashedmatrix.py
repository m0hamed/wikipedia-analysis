import re
from collections import Counter

class FeatureHashedMatrix:

  def __init__(self,buckets):
    self.buckets = buckets
    self.matrix = []

  def featurehash(self,features):
    ret = [0]*self.buckets
    counter = Counter(features)
    for feature, count in counter.items():
      h = hash(feature) % self.buckets
      ret[h] += count
    return ret

  def addrow(self,text):
    text = self.clean(text)
    words = re.split('[\s]',text)#split words on whitespaces
    # words = re.split('[\W]',text)#split words on not alphanumeric
    row = self.featurehash(words)
    self.matrix.append(row)

  def clean(self,text):
    return re.sub(r"\{\{.*?\}\}", '', text)
