import featurehashedmatrix, categoryCounter, reader
import sys, time, operator
import numpy as np
from sklearn.cluster import dbscan
from sklearn import metrics
from sklearn.metrics.pairwise import pairwise_distances

import os.path
import pickle

#call parseXML to load a feature hashed matrix, store it with pickle for faster testing
def loadMatrixPickle(count=100, buckets=100):

  xmlPath = "enwiki-20161101-pages-articles-multistream.xml"
  pickleMatrixPath = "pickle/fhmatrix-"+str(count)+"-"+str(buckets)+".pickle"
  pickleCounterPath = "pickle/counters-"+str(count)+".pickle"

  start = time.time()

  if os.path.exists(pickleMatrixPath) and os.path.exists(pickleCounterPath):
    matrix = pickle.load(open(pickleMatrixPath, "rb"))
    counter = pickle.load(open(pickleCounterPath, "rb"))
  else:
    matrix = featurehashedmatrix.FeatureHashedMatrix(buckets)
    counter = categoryCounter.CategoryCounterMap()
    reader.parseXML(xmlPath, [matrix.addrow, counter.addrow], count)
    pickle.dump(matrix, open(pickleMatrixPath, "wb"))
    pickle.dump(counter, open(pickleCounterPath, "wb"))

  print ("Loading time: %.2fs"%(time.time()-start))

  print(pickleMatrixPath)
  print(pickleCounterPath)
  return matrix, counter

# returns two objects:
#a dict per cluster, mapping (category:ratio of category number of appearances to number of articles in cluster)
#a total dict, mapping (category:ratio of category number of appearances to total number of articles)
def getCategoryAppearanceRates(matrix,db,counter):

  clusters = list(set(db[1]))#unique clusters

  clusterCategoryCounters = {}

  for cluster in clusters:#iterate over all clusters
    clusterCategoryCounters[cluster] = counter.getClusterCounter([i for i, x in enumerate(db[1]) if x==cluster])

  return clusterCategoryCounters, counter.totalCount

#iterate over clusters, compare category appearance ratios to total ratios, print significant
def findHighCategoryRates(clusterCategoryCounter,totalCategoryCounter,db,nArticles,counter):

  clusters = list(set(db[1]))
  clusterSizes = {i:float(list(db[1]).count(i)) for i in clusters}

  for cluster in clusters:# iterate over clusters
    #print stats
    print("\n\n\nCluster %d (%d) : %d categories"%(cluster,clusterSizes[cluster],len(clusterCategoryCounter[cluster])))

    if cluster >= 0:#ignore default noise cluster
      general = []
      prevalentCategories = sorted(clusterCategoryCounter[cluster].items(), key=lambda x: x[1], reverse=True)
      for categoryIndex in prevalentCategories[:5]: #iterate over five most common categories in cluster
        general.append((clusterCategoryCounter[cluster][categoryIndex[0]]/clusterSizes[cluster],totalCategoryCounter[categoryIndex[0]]/nArticles,categoryIndex[0]))

      #print 5 highest ratios
      print("Most prevalent categories:")
      for result in general:
        if result[0]>result[1]:
          print("\t%.4f > %.4f: %s"%(result[0],result[1],counter.categories[result[2]]))
        else:
          print("\t%.4f < %.4f: %s"%(result[0],result[1],counter.categories[result[2]]))


def fastCluster(clusteredCount, db, matrix):
  clusters = sorted(list(set(db[1])))
  clusterCenters = featurehashedmatrix.nplist()
  for clusterNdx in clusters:
    if clusterNdx > -1:
      cluster = [matrix[i] for i, x in enumerate(db[1]) if x==clusterNdx]
      clusterCenters.append(np.mean(cluster, axis=0))

  clusterDistances = pairwise_distances(matrix, clusterCenters,  metric='euclidean', n_jobs=-1)
  # print(clusterDistances.shape)
  appointedClusters = np.argmin(clusterDistances, axis=1)
  totalDb = (None,[]+[-1]*len(matrix))
  for article in range(len(matrix)):
    if article < clusteredCount and db[1][article] != -1:
      totalDb[1][article] = db[1][article]
    else:
      totalDb[1][article] = appointedClusters[article]

  return totalDb



def categoryAnalysis(count=1000, dbScanCount=100, buckets=100, startEps=100, samples=3):
  matrix, counter = loadMatrixPickle(count,buckets)
  sys.exit()

  #run Dbscan
  start = time.time()

  db = dbscan(matrix.matrix[:dbScanCount], eps=startEps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
  print("DBScan: eps= %.3f, min_samples=%d, %d clusters generated, %.2f%% noise, %d articles"%(startEps,samples,len(set(db[1])),100.0*list(db[1]).count(-1)/count,len(matrix.matrix)))
  print ("DBScan time: %.2fs"%(time.time()-start))

  start = time.time()

  totalDb = fastCluster(dbScanCount, db, matrix.matrix)
  print ("fastCluster time: %.2fs"%(time.time()-start))

  start = time.time()

  clusterCategoryCounter, totalCategoryCounter = getCategoryAppearanceRates(matrix,totalDb,counter)
  findHighCategoryRates(clusterCategoryCounter,totalCategoryCounter,totalDb,count,counter)

  print ("Category analysing time: %.2fs"%(time.time()-start))


def categoryAnalysisMultiDB(count=100, buckets=100, startEps=100, targetNoise=0.5, samples=3):
  matrix, counter = loadMatrixPickle(count,buckets)

  #run Dbscan
  start = time.time()

  mat = np.array(matrix.matrix)
  indexMap=list(range(len(mat)))
  totalDb = (None,[-1]*len(mat))#cluster representation returned by DBScan, modified iteratively to add more clusters

  reps = 0
  eps = startEps
  while list(totalDb[1]).count(-1)/float(count) > targetNoise:
    reps += 1
    db = dbscan(mat, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
    print("DBScan: eps= %.3f, min_samples=%d, %d clusters generated, %.2f%% noise, %d articles"%(eps,samples,len(set(db[1])),100.0*list(db[1]).count(-1)/count,len(mat)))

    removeClusters(mat,db,indexMap,totalDb)
    eps *= 1.5

  print("%d DBscans ran, %d clusters total, %.2f%% noise left"%(reps,len(set(totalDb[1])),100.0*list(totalDb[1]).count(-1)/count))
  print ("DBScan time: %.2fs"%(time.time()-start))


  start = time.time()


  clusterCategoryCounter, totalCategoryCounter = getCategoryAppearanceRates(matrix,db,counter)
  findHighCategoryRates(clusterCategoryCounter,totalCategoryCounter,db,count,counter)


  print ("Category analysing time: %.2fs"%(time.time()-start))

def removeClusters(currentMatrix,currentDb,indexMap,totalDb):
  maxCluster = max(totalDb[1])+1
  clusterSizes = {i:float(list(currentDb[1]).count(i)) for i in set(currentDb[1])}

  for cluster in set(currentDb[1]):
    if cluster >= 0:
      if clusterSizes[cluster] > 10:
        newClusterArticles =  [indexMap[index] for index, cluster_ in enumerate(currentDb[1]) if cluster_ == cluster]
        for article in newClusterArticles:
          totalDb[1][article] = cluster+maxCluster
      else: # reappoint small clusters to noise cluster
        for article in [i for i, x in enumerate(currentDb[1]) if x==cluster]:
          currentDb[1][article] = -1


  for index, cluster in reversed(list(enumerate(currentDb[1]))):
    if cluster >= 0:
      indexMap.pop(index)
      currentMatrix.pop(index)
  print(len(currentMatrix))
  print(max(totalDb[1]))


def findDBParameters(count=100, buckets=100):
  matrix, counter = loadMatrixPickle(count,buckets)
  startEps = 50
  startSamples = 2
  results = []

  for eps in range(startEps,startEps*10,5):
    for samples in range(startSamples,startSamples*2,1):
      db = dbscan(matrix.matrix, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
      clusters = list(set(db[1]))
      clusterSizes = [float(list(db[1]).count(i)) for i in clusters]
      print("eps=%03d, samples=%02d, clusters=%02d, std=%04.3f"%(eps,samples,len(clusters),np.std(clusterSizes)))
      results.append((eps,samples,len(clusters),np.std(clusterSizes)))

  resultsTopStd = sorted(results,key=lambda x:x[2],reverse=True)
  resultsTopEps = sorted(results,key=lambda x:x[3])

  print(resultsTopStd[0])
  print(resultsTopEps[0])

if __name__ == "__main__":

  #usage: dbscan.py (articleCount) (numClusters) (dbscanStartingEps) (dbscanMinSamples) (targetNoiseRatio)

  dbScanCount = 100
  count = 1000
  buckets = 100
  eps = 100
  samples = 3

  if len(sys.argv) > 5:
    dbScanCount = int(sys.argv[5])
  if len(sys.argv) > 4:
    samples = int(sys.argv[4])
  if len(sys.argv) > 3:
    eps = int(sys.argv[3])
  if len(sys.argv) > 2:
    buckets = int(sys.argv[2])
  if len(sys.argv) > 1:
    count = int(sys.argv[1])
  else:
    print("usage: dbscan.py (articleCount) (numBuckets) (dbscanStartingEps) (dbscanMinSamples) (DBScanCount) ")
    print("running with default values")


  # categoryAnalysisMultiDB(count=count,buckets=buckets,startEps=eps,targetNoise=noise,samples=samples)
  categoryAnalysis(count=count,dbScanCount=dbScanCount,buckets=buckets,startEps=eps,samples=samples)
  # findDBParameters(count=count,buckets=buckets)
