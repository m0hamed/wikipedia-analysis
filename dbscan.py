import featurehashedmatrix, reader
import sys
import numpy as np
from sklearn.cluster import dbscan
from sklearn import metrics
import os.path
import pickle

# returns a map per cluster, mapping category to number of appearances
def getClusterCategories(matrix,db):
  clusters = list(set(db[1]))
  ret = {cluster:{} for cluster in clusters}
  for i,articlecategories in enumerate(matrix.categories):
    for category in articlecategories:
      if category in ret[db[1][i]]:
        ret[db[1][i]][category] += 1
      else:
        ret[db[1][i]][category] = 1
  return ret

if __name__ == "__main__":
  if len(sys.argv) > 1:
    count = int(sys.argv[1])
  else:
    count = 50

  #call parseXML, store featurehashedmatrix with pickle for faster testing
  picklepath = "fhmatrix-"+str(count)+".pickle"
  if os.path.exists(picklepath):
    matrix = pickle.load(open(picklepath, "rb"))
  else:
    matrix = featurehashedmatrix.FeatureHashedMatrix(100)
    reader.parseXML("../enwiki-20161101-pages-articles-multistream.xml", matrix.addrow, count)
    pickle.dump(matrix, open(picklepath, "wb"))

  ### standardise the matrix for distances to make sense 
  ### TODO: is this necessary or helpful? dbscan runs nicely on list of lists from featurehashedmatrix
  mat = np.matrix(matrix.matrix)
  means = np.mean(mat, axis=0)
  stds = np.std(mat, axis=0)
  mat = (mat - means) / stds

  ### crudely figure out best eps for to produce the most clusters 
  ### or 10k articles, 0.09*mean best
  # for i in range(1,15):
  #   eps = i*0.01*np.mean(means)
  #   db = dbscan(mat, eps=eps, algorithm='kd_tree', min_samples=2, n_jobs=-1)
  #   print("eps=",eps,", ",len(set(db[1])),"clusters")

  ### crudely figure out best min_samples to produce the most clusters
  ### for 10k articles, samples=2 produces more clusters, but samples=3 produces bigger ones
  # for samples in range(2,4):
  #   eps = 0.09*np.mean(means)
  #   db = dbscan(mat, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
  #   clusterSizes = {i:list(db[1]).count(i) for i in list(set(db[1]))}
  #   print("samples=",samples,", ",len(set(db[1])),"clusters, ",clusterSizes)

  ### correlation not yet implemented:
  ### TODO: get ratio of category appearance count in all articles to number of articles
  ### TODO: copare same ratio within cluster to total ratio
  ### TODO: if ratio within cluster is higher that total, win (outliers of small clusters?)

  ### get number of categories per cluster
  eps = 0.09*np.mean(means)
  samples = 3
  db = dbscan(mat, eps=eps, algorithm='kd_tree', min_samples=samples, n_jobs=-1)
  clusterCategories = getClusterCategories(matrix,db)
  print("eps=",eps,", ",len(set(db[1])),"clusters")
  clusterSizes = {i:list(db[1]).count(i) for i in list(set(db[1]))}
  for clusterNdx in clusterCategories:
    print("cluster ",clusterNdx,"size: ",clusterSizes[clusterNdx],": ",len(clusterCategories[clusterNdx])," categories")
