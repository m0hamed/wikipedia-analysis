import re
import reader
import numpy as np

class FeatureHashedMatrix:

  def __init__(self,buckets):
    self.buckets = buckets
    self.matrix = nplist();

  def featurehash(self,features):
    ret = [0]*self.buckets
    for feature in features:
      h = hash(feature) % self.buckets
      ret[h] += 1
    return ret

  def addrow(self,text,_):
    text = self.clean(text)
    words = re.split('[\s]',text)#split words on whitespaces
    # words = re.split('[\W]',text)#split words on not alphanumeric
    ### TODO: empty strings from split?
    row = nplist(self.featurehash(words))
    self.matrix.append(row)

  def clean(self,text):
    return re.sub(r"\{\{.*?\}\}", '', text)

class nplist:

  def __init__(self,listin=[]):
    self.list = listin
    if hasattr(listin, '__len__') and len(listin) > 0 and hasattr(listin[0], '__len__'):
      self.shape = (len(listin),len(listin[0]))
    else:
      self.shape = ()

  def __getitem__(self, key):
    ret = self.list[key]
    if hasattr(ret, '__getitem__'):
      return nplist(ret)
    return ret

  def __iter__(self):
    return self.list.__iter__()

  def __len__(self):
    return self.list.__len__()

  def __repr__(self):
    return self.list.__repr__()

  def __str__(self):
    return self.list.__str__()

  def append(self,thingy):
    self.list.append(thingy)
    if len(self.shape) == 2:
      self.shape = (self.shape[0]+1,self.shape[1])
    elif hasattr(thingy, '__len__') and len(thingy) > 0:
      self.shape = (1,len(thingy))

