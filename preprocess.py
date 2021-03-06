# -*- coding: utf-8 -*-
"""
Created on Tue Oct 04 23:03:51 2016

@author: SYARLAG1
"""

import os
import numpy as np

os.chdir('C:/Users/syarlag1/Desktop/Label-Distribution-Metric-Learning')
#os.chdir('/Users/Sriram/Desktop/DePaul/Label-Distribution-Metric-Learning/data')

from metricLearningFunctions import *

###################Initial Data Exploration####################################
metrics = ['cosine', 'fidelity', 'intersection', 'euclidean', 'sorensen', 'squaredChiSq',\
               'chebyshev', 'clark', 'canberra','KL']


#trial = np.array([[0.1, 0.2, 0.3, 0.4],[0.5, 0.5, 0, 0], [0.1, 0.3, 0.6, 0], [0.2, 0.4, 0.1, 0.3]])
#metricStats(metrics, trial)

os.chdir('./data')

labelsList = []; labelsDict = {};
for fileName in os.listdir('./'):
    if 'Label' in fileName:
        labelsDict[fileName] = np.genfromtxt(fileName, delimiter=',')
        labelsList.append(fileName)
    if 'LIDC' in fileName:
        labelsDict[fileName] =  np.genfromtxt(fileName, delimiter = ',',\
        skip_header = 1, usecols = (84,93,102,111)).astype(int)
        labelsList.append(fileName)
labelsList

smallerLabelsList = ['SJALabels.csv','naturalSceneLabels.csv', 'YeastSPOEMLabels.csv',\
 'YeastHeatLabels.csv', 'YeastSPOEMLabels.csv', 'LIDC_REU2015.csv' ]
metricLst = ['cosine', 'fidelity','intersection','euclidean','chebyshev', 'sorensen', 'squaredChiSq']





##################Pre-Processing For Metric Learning###########################
################Generating Sim and Dist Matrices###############################
os.chdir('./data')

X_data = np.genfromtxt('./LIDC_REU2015.csv', delimiter = ',', skip_header = 1 , usecols = (range(11,76)))
Y_data = np.genfromtxt('./LIDC_REU2015.csv', delimiter = ',', skip_header = 1, usecols = (84,93,102,111)).astype(int)

X_data = np.genfromtxt('./naturalSceneFeatures.csv', delimiter = ',')
Y_data = np.genfromtxt('./naturalSceneLabels.csv', delimiter = ',')

X_data = np.genfromtxt('./SJAFeatures.csv', delimiter = ',')
Y_data = np.genfromtxt('./SJALabels.csv', delimiter = ',')

trainX, trainY, testX, testY = splitTrainTest(X_data,Y_data,0.7,99)

# if using percentiles (default is True), set negFill = False
X,S,D,R = genSimDistRatioMats(data = trainX, targetArray = trainY, negFill=False) 

os.chdir('./..')

np.savetxt('./S.csv',S,delimiter=',')
np.savetxt('./R.csv', R,delimiter=',')

NN3_Ws = findKNeighbourhood(S,D,R,k=3)
pullMat, pushMat = pullPushMats(NN3_Ws, R, 3)


np.savetxt('./pull.csv',pullMat,delimiter=',')
np.savetxt('./push.csv',pushMat,delimiter=',')

#####Checks:
np.mean(S)

np.std(S)   
count = 0
for i in range(NN3_Ws.shape[0]): #to make verify size of nei
   if len(set(NN3_Ws[i])) <= 3: count += 1
   
for i in range(R.shape[0]):  #to verify if there are nans
    if sum(np.isnan(R[i]))>0: print i

count = 0
for i in range(D.shape[0]): #to verify if there is anything closer than 0.0001
    if np.amin(D[i])<0.0001: print np.amin(D[i]); count += 1

count = 0
for i in range(NN3_Ws.shape[0]): #to make verify size of nei
   if sum(np.array(list(set(NN3_Ws[i]))>0.5))>0: print set(NN3_Ws[i]); count +=1
########
