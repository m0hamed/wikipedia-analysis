import re
import reader
from collections import Counter

class CategoryCounter:

  def __init__(self):
    self.categories = []
    self.total = Counter()

  def addrow(self,text,_):
    categories = reader.extractCategories(text)
    newCounter = Counter(categories)
    self.categories.append(newCounter)
    self.total.update(categories)

  def getClusterCounter(self,clusterIndices):
    counterList = [self.categories[i] for i in clusterIndices]
    return sum(counterList, Counter())

class CategoryCounterMap:

  def __init__(self):
    self.categories = {}
    self.categoryIndices = {}
    self.articleCounts = []
    self.totalCount = {}

  def addrow(self,text,_):
    articleCategories = reader.extractCategories(text)
    articleCount = {}
    for category in articleCategories:
      if category in self.categoryIndices:
        self.totalCount[self.categoryIndices[category]] += 1
        if self.categoryIndices[category] in articleCount:
          articleCount[self.categoryIndices[category]] += 1
        else:
          articleCount[self.categoryIndices[category]] = 1
      else:
        self.categoryIndices[category] = len(self.categoryIndices)
        self.categories[self.categoryIndices[category]] = category
        self.totalCount[self.categoryIndices[category]] = 1
        articleCount[self.categoryIndices[category]] = 1
    self.articleCounts.append(articleCount)

  def getClusterCounter(self,clusterIndices):
    clusterCounts = {}
    for article in clusterIndices:
      for categoryIndex in self.articleCounts[article]:
        if categoryIndex in clusterCounts:
          clusterCounts[categoryIndex] += self.articleCounts[article][categoryIndex]
        else:
          clusterCounts[categoryIndex] = self.articleCounts[article][categoryIndex]
    return clusterCounts