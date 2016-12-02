import featurehashedmatrix, reader
import sys, time, operator
import numpy as np
from sklearn.cluster import dbscan
from sklearn import metrics
import os.path
import pickle

#call parseXML to load a feature hashed matrix, store it with pickle for faster testing
def loadMatrixPickle(count=100, nClusters=100):

  xmlPath = "enwiki-20161101-pages-articles-multistream.xml"
  picklepath = "fhmatrix-"+str(count)+"-"+str(nClusters)+".pickle"

  if os.path.exists(picklepath):
    matrix = pickle.load(open(picklepath, "rb"))
  else:
    matrix = featurehashedmatrix.FeatureHashedMatrix(nClusters)
    reader.parseXML(xmlPath, matrix.addrow, count)
    pickle.dump(matrix, open(picklepath, "wb"))
  print(picklepath)
  return matrix

# returns two objects:
#a dict per cluster, mapping (category:ratio of category number of appearances to number of articles in cluster)
#a total dict, mapping (category:ratio of category number of appearances to total number of articles)
def getCategoryAppearanceRates(matrix,db):
  nArticles = float(len(matrix.matrix))#number of articles in total

  clusters = list(set(db[1]))#unique clusters

  clusterSizes = {cluster:float(list(db[1]).count(cluster)) for cluster in clusters}

  clusterCategories = {cluster:{} for cluster in clusters}
  totalCategories = {}

  for i,articlecategories in enumerate(matrix.categories):#iterate over all articles
    for category in articlecategories:#iterate over article's categories
      #add a category appearance to that cluster
      if category in clusterCategories[db[1][i]]:
        clusterCategories[db[1][i]][category] += 1
      else:
        clusterCategories[db[1][i]][category] = 1
  for cluster in clusterCategories:# iterate over clusters
    for category in clusterCategories[cluster]: #iterate over cluster's categories
      #add ratio category appearances in cluster over total articles to total category appearances
      if category in totalCategories:
        totalCategories[category] += clusterCategories[cluster][category]/nArticles
      else:
        totalCategories[category] = clusterCategories[cluster][category]/nArticles
      #convert category appearances in cluster to ratio as well
      clusterCategories[cluster][category] /= clusterSizes[cluster]

  return clusterCategories,totalCategories

#iterate over clusters, compare category appearance ratios to total ratios, print significant
def findHighCategoryRates(clusterCategoryRates,totalCategoryRate,db):
  clusterSizes = {i:list(db[1]).count(i) for i in list(set(db[1]))}
  for clusterNdx in clusterCategoryRates:# iterate over clusters
    #print stats
    print("\n\n\nCluster %d (%d) : %d categories"%(clusterNdx,clusterSizes[clusterNdx],len(clusterCategoryRates[clusterNdx])))

    if clusterNdx > 0:#ignore default noise cluster
      results = []
      for category in clusterCategoryRates[clusterNdx]: #iterate over five most common categories in cluster
        #TODO: maybe compare to find significantly larger ratios?
        #TODO: maybe filter out clusters with few articles?
        if clusterCategoryRates[clusterNdx][category] > totalCategoryRate[category]: #compare cluster ratio to total
          results.append((clusterCategoryRates[clusterNdx][category],totalCategoryRate[category],category))
      #sort results, highest appearance ratio to lowest
      results = sorted(results,key=lambda x:x[0],reverse=True)
      #print 5 highest ratios
      for result in results[:5]:
        print("\t%.4f > %.4f: %s"%result)


def categoryAnalysis(count=100, nClusters=100, eps=100, samples=3):
  matrix = loadMatrixPickle(count,nClusters)

  ### standardise the matrix for distances to make sense
  ### TODO: is this necessary or helpful? dbscan runs nicely on list of lists from featurehashedmatrix
  mat = np.matrix(matrix.matrix)
  means = np.mean(mat, axis=0)
  stds = np.std(mat, axis=0)
  # mat = (mat - means) / stds

  #run Dbscan
  start = time.time()
  db = dbscan(mat, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=4)
  print("eps= %.3f, min_samples=%d, %d clusters generated, %.2f%% noise"%(eps,samples,len(set(db[1])),100.0*list(db[1]).count(-1)/count))
  print ("DBScan time: %.2fs"%(time.time()-start))

  start = time.time()
  clusterCategoryRates,totalCategoryRate = getCategoryAppearanceRates(matrix,db)
  findHighCategoryRates(clusterCategoryRates,totalCategoryRate,db)
  print ("Category analysing time: %.2fs"%(time.time()-start))



if __name__ == "__main__":
  #usage: dbscan.py (articleCount) (numClusters) (dbscanEps) (dbscanMinSamples)
  if len(sys.argv) > 4:
    samples = int(sys.argv[4])
  if len(sys.argv) > 3:
    eps = int(sys.argv[3])
  if len(sys.argv) > 2:
    nClusters = int(sys.argv[2])
  if len(sys.argv) > 1:
    count = int(sys.argv[1])
  else:
    count = 100
    nClusters = 100
    eps = 100
    samples = 3

  categoryAnalysis(count=count,nClusters=nClusters,eps=eps,samples=samples)


  ### crudely figure out best eps for to produce the most clusters
  ### for 10k articles, with standardization, 0.09*mean seems good
  ### for 10k articles, no standardization, 100 maybe?
  # for i in range(15,25):
  #   eps = i*0.1*np.mean(means)
  #   samples = 3
  #   db = dbscan(matrix.matrix, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
  #   print("eps= %.3f, min_samples=%d, %d clusters generated, %.2f%% noise"%(eps,samples,len(set(db[1])),100.0*list(db[1]).count(-1)/count))

  ### crudely figure out best min_samples to produce the most clusters
  ### for 10k articles, samples=2 produces more clusters, but samples=3 produces bigger ones
  # for samples in range(2,4):
  #   eps = 0.09*np.mean(means)
  #   db = dbscan(matrix.matrix, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
  #   clusterSizes = {i:list(db[1]).count(i) for i in list(set(db[1]))}
  #   print("eps= %.3f, min_samples=%d, %d clusters generated, %.2f%% noise"%(eps,samples,len(set(db[1])),100.0*list(db[1]).count(-1)/count))
