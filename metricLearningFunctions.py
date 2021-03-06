# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 21:18:48 2016

@author: syarlag1
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
from sklearn.preprocessing import MinMaxScaler
plt.style.use('ggplot')
###############FUNCTIONS############################
# please note that most functions auto-detect LIDC data and gen the distribution labels
# return distribution labels for the LIDC-like datasets
def createDistributionLabels(targetArray):
    distributionLabel = []
    for entry in targetArray:
        labelVal = {1:0,2:0,3:0,4:0,5:0}#Initialize all 5 labels as 0s
        for rating in labelVal.keys():
            for radRating in entry:
                if rating == radRating:
                    labelVal[rating] += 0.25
        distributionLabel.append(labelVal.values())
    return np.array(distributionLabel)
    

# returns matrix for various sim and dist metrics
# Gaussian currently doesnt generate the percentiles
# if percentile is selected, returns array instead of matrix
def genSimDistMat(measure, labels, labelsDict = None, sigma=None, labelDistribution = True, percentile=True, negFill=True): 
    
    if type(labels) == str: Y = labelsDict[labels]
    else: Y = labels 
    if labelDistribution == False: Y = createDistributionLabels(Y)   
        
    S = np.zeros(shape=[Y.shape[0], Y.shape[0]])
    if negFill: S.fill(-1) # this is needed to remove the lower triangle values
    if measure == 'gaussian': return gaussSimMatrix(labels, labelsDict, sigma)[0]
    for i in range(S.shape[0]):
        for j in range(i+1, S.shape[0]):#changing to calculate only upper triangle
            if measure == 'cosine': S[i,j] = np.dot(Y[i],Y[j])/(np.linalg.norm(Y[i])*np.linalg.norm(Y[j]))
            if measure == 'fidelity': S[i,j] = np.sum(np.sqrt(np.multiply(Y[i],Y[j])))
            if measure == 'intersection': S[i,j] =  np.sum(np.minimum(Y[i],Y[j]))   
            if measure == 'euclidean': S[i,j] = np.sqrt(np.dot((Y[i]-Y[j]),(Y[i]-Y[j])))
            if measure == 'sorensen': S[i,j] = np.sum(np.abs(Y[i]-Y[j]))/(np.sum(Y[i]+Y[j])) 
            if measure == 'squaredChiSq': S[i,j] = np.sum(np.square(Y[i]-Y[j])/(Y[i]+Y[j]))
            if measure == 'chebyshev': S[i,j] = np.max(np.abs(Y[i] - Y[j]))            
            if measure == 'clark': S[i,j] =  np.sqrt(np.sum(np.square(Y[i]-Y[j])/np.square((Y[i]+Y[j]))))
            if measure == 'canberra': S[i,j] = np.sum(np.abs(Y[i]-Y[j])/((Y[i]+Y[j])))
            if measure == 'KL':
                tempSum = 0
                for k in range(len(Y[i])):
                    tempSum += Y[i,k]*(np.log((Y[i,k] if Y[i,k]>0 else 0.01)/(Y[j,k] if Y[j,k]>0 else 0.01)))
                S[i,j] = tempSum
    if percentile:
        return convertMatToPercentile(S, negFill)
    return S

# returns a Gaussian similarity matrix
def gaussSimMatrix(labels,labelsDict, sigma=None):
    Y=labels    
    euclideanSimMat =  genSimDistMat('euclidean',Y, labelsDict,  percentile=False)
    if sigma is None: sigma = np.nanstd(euclideanSimMat)
    return np.exp(-euclideanSimMat**2/(2*(sigma)**2)), sigma  
        
# returns important stats for the labels
def metricStats(metricList, labels, labelsDict, percentile):
    mean = []; std = []; maxLst = []; minLst = []; nanCount = []
    if 'LIDC' in labels: labelDistribution = False
    else: labelDistribution = True    
    for metric in metricList: # Nan values are ignored when calculating the performance
        S = genSimDistMat(metric, labels, labelsDict, percentile=percentile, labelDistribution=labelDistribution)
        nanCount.append(np.sum(np.isnan(S)))        
        S = S.flatten()
        S = S[S>=0] # to remove lower triangle values
        mean.append(np.nanmean(S))       
        std.append(np.nanstd(S))
        maxLst.append(np.nanmax(S))
        minLst.append(np.nanmin(S))
    combinedList = zip(metricList, mean, std, maxLst, minLst, nanCount)
    colNames = ['Metric', 'Mean', 'StdDev', 'MaxValue', 'MinValue', 'NanCount']
    return pd.DataFrame(combinedList, columns = colNames)
    
# return a percentile matrix for the inputted matrix
# negFill=True returns array. False returns matrix
def convertMatToPercentile(S, negFill):
    if negFill:    
        arr = S.flatten();
        arr = arr[arr>=0] # to remove lower triangle values
    else:
        originalShape = S.shape
        arr = S.flatten()    
        
    sortedUniqueArr = np.unique(np.sort(arr))
    percentileArr = np.linspace(0.01,0.99,len(sortedUniqueArr))
    percentileValueDict = {x:percentileArr[i] for i,x in enumerate(sortedUniqueArr)}
    percentileArr = np.array([percentileValueDict[x] for x in arr])
    
    if negFill: return percentileArr
    else: return np.reshape(percentileArr, originalShape)
   
# returns stats for each element in the list
def metricStatsforLabelList(metricList, labelsList, labelsDict,  percentile):
    resultDict = {}
    for labels in labelsList:
        result = metricStats(metricList, labels, labelsDict, percentile)
        resultDict[labels] = result
        print labels
        print result
        print '\n'
    return resultDict

# prints histograms for the inputted matrices
def histCreator(metricList, labelsList, labelsDict, bins, percentile):
    for metric in metricList:
        for label in labelsList:
            figName = metric + '-' + label + '.png'
            if 'LIDC' in label: labelDistribution = False
            else: labelDistribution = True    
            S = genSimDistMat(metric, label, labelsDict,\
            labelDistribution=labelDistribution, percentile=percentile)
            S = S.flatten()
            S = S[S>=0]            
            plt.figure()
            plt.hist(S[~np.isnan(S)], bins=bins)
            plt.title(figName)
            plt.savefig(figName)
    return            
        
# returns a test-train split of data and labels
def splitTrainTest(data,Labels,train_percent,random_state, minmax=False):
    random.seed(random_state)
    indexList = range(len(data))
    random.shuffle(indexList)
    trainIndexList = indexList[:int(len(data)*train_percent)]
    testIndexList = indexList[int(len(data)*train_percent):] 
    train, trainLabels, test, testLabels = data[trainIndexList], Labels[trainIndexList], data[testIndexList], Labels[testIndexList]
    if minmax:
        fit = MinMaxScaler.fit(train)
        train = fit.transform(train)
        test = fit.transform(test)
    return train, trainLabels, test, testLabels

# returns the data(X), Label Similarity(S), Feature Dist(D), S/R (R)  matrices
## currently only calculates cosine sim and dist 
def genSimDistRatioMats(data, targetArray, alpha = 1, LabelDistribution = True, percentile=True, negFill=False): 
    X = data  
    S = (genSimDistMat('cosine',targetArray,labelDistribution=LabelDistribution, percentile=percentile,negFill=negFill))**alpha
    D = (1 - genSimDistMat('cosine',X,labelDistribution=LabelDistribution, percentile=percentile,negFill=negFill))**alpha 
    R = S/D
    np.fill_diagonal(S,0); np.fill_diagonal(D,1); np.fill_diagonal(R,0) # filling diagnols with 0 and 1
    return X, S, D, R

# returns a matrix of the top k-neighbours for each data point
def findKNeighbourhood(S,D,R,k=3, returnType = 'sim'):
    neiWeights=np.zeros(shape=S.shape) # initialize zero matrix
    for i in range(S.shape[0]): 
        indices = (R[i]).argsort()[-k:] # get the indices of the 3 largest R's
        targetDist = np.amax(D[i,indices]) # get the corresponding distances and find the largest dist
        # return ratio or sim if less than dist else 0 
        if returnType=='sim':
            neiWeights[i]=np.array([S[i,index] if x<=float(targetDist) else 0 for index,x in enumerate(D[i])]) 
        if returnType=='ratio':        
            neiWeights[i]=np.array([R[i,index] if x<=float(targetDist) else 0 for index,x in enumerate(D[i])]) 
    return neiWeights


# returns the push neighbourhood and the pull neighbourhood matrices
def pullPushMats(Nei, R, k):
    pushMat = np.zeros(shape=R.shape) # initialize the push and pull matrices
    pullMat = np.zeros(shape=R.shape)
    for i in range(R.shape[0]): 
        indices = (R[i]).argsort()[-k:] # get the indices of the 3 largest R's     
        pullMat[i] = np.array([NeiVal if iNei in indices else 0 for iNei, NeiVal in enumerate(Nei[i])])
        tempArr = Nei[i]; tempArr[indices] = 0 # set 
        pushMat[i] = tempArr
    return pullMat, pushMat


# returns the distances matrices to be implemented in cvx
def createWeightedDistanceMatrices(Nei, X):
   d_ij_S = np.zeros(shape=[X.shape[0],X.shape[0],X.shape[1]])

   for i in range(X.shape[0]):
       for j in range(i+1, X.shape[0]):
        d_ij_S[i,j,:] = Nei[i,j]*np.square(np.array(X[i]-X[j])) # x_i - x_j vector mulitplied by its weight 
   
   return d_ij_S

# transformed X using Matrix factorization for the optimization output
def XTransform(M, X):
    L = np.linalg.cholesky(M)
    return np.dot(X,L)

