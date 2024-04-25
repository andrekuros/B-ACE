#%%%
"""
Created on Mon Jul  4 12:15:38 2022

@author: andre
"""
import json
import numpy as np
import wget
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
#import psycopg2.extras
import pandas.io.sql as sqlio
import math
import os
import matplotlib.cm as cm
import time
import itertools
#import statsmodels.api as sm
import time
#from bioinfokit.analys import stat
import scipy.stats as stats
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle
from sklearn.preprocessing import MinMaxScaler
from sklearn.kernel_approximation import Nystroem
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
import sklearn
from sklearn.svm import SVR
from sklearn.preprocessing import PolynomialFeatures
import scipy.stats as stats
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle
from sklearn.preprocessing import MinMaxScaler
from sklearn.kernel_approximation import Nystroem
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
import sklearn
from sklearn.svm import SVR
from sklearn.preprocessing import PolynomialFeatures
from sklearn.neural_network import MLPRegressor
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from itertools import combinations_with_replacement 
from sklearn.ensemble import  RandomForestRegressor

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import KFold
from numpy import sqrt

#Force the Working Directory for the file directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

import warnings
warnings.filterwarnings("ignore")

plt.rcParams["font.size"] = 8
   
extraTime = 15 #Flight Time before achieve launch coords
latRef = 0.0
lonRef = 0.0

g2rad = math.pi / 180
m2nm = 1/1852
nm2m = 1852 
feet2m = 0.3048
pi = math.pi
refCols = ["A","B","C","D","E",'Fcos',"Fsen","H","I","J","K"] 
rangeEval = 1 # 1-> RMAX / 2->RNEZ

def prepareDataFromASA(fileName, altInMeters = False, relativeRedHdg = True,\
                        normalize = True, argumentation = True, size = -1,  \
                        sinCos = True):
        
    fulldataDf = pd.read_csv(fileName)   
    
    if size > 0:
        fulldataDf = fulldataDf.sample(size)
        
    dataDf = fulldataDf[['BL_Speed', 'RD_Speed', 'rad', 'RD_Hdg', 'BL_Alt', 'RD_Alt']]
    
    dataDf['maxRange'] = fulldataDf['maxRange']
    dataDf['maxRange'].replace(-1,0)
    dataDf = dataDf[dataDf['maxRange'] > 1] 
     
    if argumentation:                
        #dataDf = dataDf[dataDf['rad'] <= 0]        
        dataDf_Arg = dataDf.copy()
        dataDf_Arg['rad'] = dataDf_Arg.apply(lambda x: -1 * x.rad , axis=1)  
        dataDf_Arg['RD_Hdg'] = dataDf_Arg.apply(lambda x: -1 * x.RD_Hdg , axis=1)         
        dataDf = pd.concat([dataDf, dataDf_Arg], axis=0, ignore_index=True)        
        
    if altInMeters:
        dataDf['diffAlt'] = dataDf.apply(lambda x: x.BL_Alt - x.RD_Alt, axis=1)      
    else:    
        dataDf['diffAlt'] = dataDf.apply(lambda x: (x.BL_Alt - x.RD_Alt)*feet2m, axis=1)  
        dataDf['BL_Alt'] = dataDf.apply(lambda x: (x.BL_Alt)*feet2m, axis=1)          
                
    if relativeRedHdg:
        #dataDf['relRedHdg'] = dataDf.apply(lambda x: (x.RD_Hdg-x.rad) * ( 1 if x.rad < 0 else -1), axis=1) 
        dataDf['relRedHdg'] = dataDf.apply(lambda x: (x.RD_Hdg-x.rad) , axis=1) 
        if sinCos:
            dataDf['cosRel'] = dataDf.apply(lambda x: math.cos(x.relRedHdg*math.pi/180), axis=1)
            dataDf['sinRel'] = dataDf.apply(lambda x: math.sin(x.relRedHdg*math.pi/180), axis=1) 
            #dataDf['cosRel2'] = dataDf.apply(lambda x: math.cos(x.rad*math.pi/180), axis=1)
            #dataDf['sinRel2'] = dataDf.apply(lambda x: math.sin(x.rad*math.pi/180), axis=1)        
    
    else:     
        dataDf['relRedHdg'] = dataDf.apply(lambda x: 0-x.RD_Hdg , axis=1)
        if sinCos:
            dataDf['cosRel'] = dataDf.apply(lambda x: math.cos(x.relRedHdg*math.pi/180), axis=1)
            dataDf['sinRel'] = dataDf.apply(lambda x: math.sin(x.relRedHdg*math.pi/180), axis=1)
            dataDf['cosRel2'] = dataDf.apply(lambda x: math.cos(x.rad*math.pi/180), axis=1)
            dataDf['sinRel2'] = dataDf.apply(lambda x: math.sin(x.rad*math.pi/180), axis=1)
            #dataDf = dataDf.drop(['rad'], axis =1)                                                          
    
    dataDf = dataDf.drop(['RD_Hdg'], axis =1)     
    dataDf = dataDf.drop(['RD_Alt'], axis =1) 
    
    if sinCos:
        dataDf = dataDf.drop(['relRedHdg'], axis=1)                          
    
    
    
    #dataDf = dataDf[dataDf['cosRel'] > 0.80 ]
    #dataDf = dataDf[dataDf['cosRel'] < -0.90]
    
    #dataDf = dataDf[dataDf['sinRel'] > 0.90 ]
    #dataDf = dataDf[dataDf['sinRel'] < -0.90]
    
    #dataDf = dataDf[dataDf['rad'] <= 0]
    #dataDf = dataDf[dataDf['BL_Speed'] > 450]
    #dataDf = dataDf[dataDf['BL_Speed'] < 750]
    
    #dataDf = dataDf[dataDf['RD_Hdg'] <= 0]
    #dataDf = dataDf[dataDf['RD_Hdg'] > 450]
    #dataDf = dataDf[dataDf['RD_Hdg'] < 750]     
    
    #dataDf = dataDf[dataDf['RD_Speed'] > 450]
    #dataDf = dataDf[dataDf['RD_Speed'] < 750]
    
    #dataDf = dataDf[dataDf['diffAlt'] < 5000]
    #dataDf = dataDf[dataDf['diffAlt'] > -5000]
    
    #dataDf = dataDf[dataDf['BL_Alt'] > 1000 * utils.feet2m ]
    #dataDf = dataDf[dataDf['BL_Alt'] < 45000* utils.feet2m ]
    
    if normalize:        
        dataDf['BL_Alt'] = dataDf['BL_Alt'] / max(abs(dataDf['BL_Alt']))
        dataDf['diffAlt']  = dataDf['diffAlt'] / max(abs(dataDf['diffAlt']))
        dataDf['BL_Speed'] = dataDf['BL_Speed'] / max(abs(dataDf['BL_Speed']))
        dataDf['RD_Speed']  = dataDf['RD_Speed'] / max(abs(dataDf['RD_Speed']))
        dataDf['rad']  = dataDf['rad'] / max(abs(dataDf['rad']))
        if not sinCos:
            dataDf['relRedHdg'] = dataDf['relRedHdg'] / max(abs(dataDf['relRedHdg']))     
    
    return dataDf

def prepareDataFromGodot(fileName, altInMeters = False, relativeRedHdg = True, normalize = True):
        
    fulldataDf = pd.read_csv(fileName)      
    
    #dataDf = fulldataDf[['BL_Speed', 'RD_Speed', 'rad', 'RD_Hdg', 'BL_Alt', 'RD_Alt']]
    dataDf = fulldataDf[['blue_alt','red_alt','angle_off','aspect_angle']]

    #dataDf = dataDf[dataDf['aspect_angle'] >= -15]
    #dataDf = dataDf[dataDf['aspect_angle'] <= 15]
    
    
    #dataDf = dataDf[dataDf['aspect_angle'] < 750]  
    
    if altInMeters:
        dataDf['diffAlt'] = dataDf.apply(lambda x: x.blue_alt - x.red_alt, axis=1)     
    else:    
        
        dataDf['diffAlt'] = dataDf.apply(lambda x: (x.blue_alt - x.red_alt)*feet2m, axis=1) 
        #dataDf = dataDf[dataDf['diffAlt'] > -5000*feet2m]
        #dataDf = dataDf[dataDf['diffAlt'] < 10000*feet2m]
            
        dataDf['blue_alt'] = dataDf.apply(lambda x: (x.blue_alt)*feet2m, axis=1)       
    
    if relativeRedHdg:
         #dataDf['relRedHdg'] = dataDf.apply(lambda x: (x.RD_Hdg-x.rad) * ( 1 if x.rad < 0 else -1), axis=1) 
        #dataDf['relRedHdg'] = dataDf.apply(lambda x: (x.RD_Hdg-x.rad) , axis=1) 
        dataDf['relRedHdg'] = dataDf['aspect_angle'] #/ 180.0 * math.pi
        dataDf['cosAspect']    = dataDf.apply(lambda x: math.cos(x.relRedHdg * math.pi / 180.0), axis=1)
        dataDf['sinAspect']    = dataDf.apply(lambda x: math.sin(x.relRedHdg * math.pi/ 180.0), axis=1)         
    
        dataDf['relRedHdg2'] = dataDf['angle_off'] #/ 180.0 * math.pi
        dataDf['cosAngleOff']    = dataDf.apply(lambda x: math.cos(x.relRedHdg2 * math.pi/ 180.0), axis=1)
        dataDf['sinAngleOff']    = dataDf.apply(lambda x: math.sin(x.relRedHdg2 * math.pi/ 180.0), axis=1)         
                                                         
    #dataDf['angle_off'] = dataDf['angle_off'] / 180 * math.pi
    #dataDf['red_alt'] = dataDf['red_alt'] / 50000
    #dataDf['aspect_angle'] = dataDf['aspect_angle'] / 180 * math.pi
    dataDf = dataDf.drop(['red_alt'], axis =1)               
    dataDf = dataDf.drop(['aspect_angle'], axis =1)               
    dataDf = dataDf.drop(['angle_off'], axis =1)               
    dataDf = dataDf.drop(['relRedHdg'], axis=1)            
    dataDf = dataDf.drop(['relRedHdg2'], axis=1)            
    #dataDf = dataDf.drop(['red_alt'], axis =1) 
    
    if normalize:        
        dataDf['blue_alt'] = dataDf['blue_alt'] / 50000
        dataDf['diffAlt']  = dataDf['diffAlt'] / 50000
                                                         
                      
        
    dataDf['maxRange'] = fulldataDf['Rmax'] * -1
    #dataDf['maxRange'].replace(-1,0)
    #dataDf = dataDf[dataDf['maxRange'] > 1] 

    

    return dataDf


def plotBoxPlots(dataDf):
        
    refCols = ["A","B","C","D","E","F",'Fcos',"Fsen","H","I","J","K"] 
    dataDf.columns = refCols[:len(dataDf.columns)-1] + ['Rmax']
    
    
    for i,col in enumerate(dataDf.columns[:-1]):
        subplot = math.ceil((len(dataDf.columns)/3))* 100 + 30 + i + 1
        ax = plt.subplot(subplot)
        boxplot = dataDf.boxplot(column=["Rmax"],by=[col],ax=ax,  layout=(6,3))
        plt.subplots_adjust(top = 0.9, bottom=0.05, hspace=0.6, wspace=0.2)
        
    plt.suptitle('')
    
def runTukeyTest(dataDf, listOfFactors):
        
    from statsmodels.stats.multicomp import pairwise_tukeyhsd    
    for col in listOfFactors:       
        tukey = pairwise_tukeyhsd(endog=dataDf['maxRange'],
                              groups=dataDf[col],
                              alpha=0.05)
        print(tukey)
        

def evalData(dataType, model_label, interactionsDegree, polyReductionFactors, regressor, X, Y, printData=True, dnn = False, timeReps = 200):
    
    #Eval on Training set
    start = time.time()
    
    for i in range(timeReps):
        y_pred = regressor.predict(X)     
    predTime = time.time() - start  
    
    if not dnn:
        r2 = regressor.score(X, Y)
        maxError = max( abs(Y - y_pred)) 
    else:
        r2 = 0
        maxError = 0
    
    mae = mean_absolute_error(Y, y_pred)
    mse = mean_squared_error(Y, y_pred)
    rmse = math.sqrt(mse)
    
    
    if printData:
        print(f'{dataType}')
        print(f'MAE:{mae} RMSE: {rmse} R2: {r2} MaxError: {maxError}')
        print(f'fitTime:{fitTime}  -  PredTime:{predTime}')
        
    return [dataType, model_label,interactionsDegree, polyReductionFactors, mae, rmse, r2, maxError, fitTime, predTime, y_pred]

def computeDnn():
    
    act_type = 'tanh'
    net = 2
    # Define the model architecture
    model = Sequential()
    
    #input layer
    model.add(Dense(units=len(X_trainS.columns),activation=act_type))
    
    #hidden layers
    if net == 1:
        model.add(Dense(units=512,activation=act_type))
        model.add(Dense(units=512,activation=act_type))
        model.add(Dense(units=256,activation=act_type))
        model.add(Dense(units=256,activation=act_type))
        model.add(Dense(units=128,activation=act_type))
        model.add(Dense(units=128,activation=act_type))
        model.add(Dense(units=64,activation=act_type))
        model.add(Dense(units=64,activation=act_type))
        model.add(Dense(units=32,activation=act_type))
        model.add(Dense(units=32,activation=act_type))
    else:
        model.add(Dense(units=32,activation=act_type))
        model.add(Dense(units=32,activation=act_type))
        model.add(Dense(units=16,activation=act_type))
        model.add(Dense(units=16,activation=act_type))
        model.add(Dense(units=8,activation=act_type))
        model.add(Dense(units=8,activation=act_type))
        model.add(Dense(units=4,activation=act_type))
        model.add(Dense(units=4,activation=act_type))
        model.add(Dense(units=2,activation=act_type))
        model.add(Dense(units=2,activation=act_type))
                
    #output layer
    model.add(Dense(units=1))
    
    early_stop = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=50)
    
    # Compile the model for a regressionn problem
    model.compile(loss='mse', optimizer='adam', metrics=[MeanAbsoluteError(),MeanSquaredError(),RootMeanSquaredError()])

    # Generate a print
    print('------------------------------------------------------------------------')
    print(f'Training for fold {fold} ...')
    
    # Fit data to model
    history = model.fit(X_trainS, Y_train,
          epochs=10000,
          batch_size=32,
          validation_data=(X_testS, Y_test), 
          callbacks=[early_stop])            
    # Generate generalization metrics
    #y_pred = model.predict(X_test)                
    #metrics.append(evalData("Train Data", "DNN", model, X_trainS, Y_train, printPartial) + [tSize])                                  
    #metrics.append(evalData("Test Data", "DNN",model, X_testS, Y_test, printPartial)+ [tSize])                    
    #mean_residual.append(Y_test -' metrics[-1][-1])  


#%%%
# Run or Complete a Batch Experiment for WEZ validation
tagName = "ASA_WEZ"
rangeType = "Rmax"

dir = './Data/Wez_Paper/'
#dataFile = "RandomExperiment_1000_cases__7392.csv" #fileName
#dataFile = 'FactorialExperiment_333334_7397.csv'
#dataFile = 'RandomExperiment_RNez_2800_cases_toASA__7403.csv'
#dataFile = 'RandomExperiment_RMax_2800_cases_toASA__7402.csv'
#dataFile = 'RandomExperiment_1000_cases__7396_Rad-60_60.csv'
dataFile = 'RandomExperiment_1000_cases__7399.csv'
#AlternateTestData = 'RandomExperiment_1000_cases__7396_Rad-60_60.csv'
#dataFile = 'wez_out.csv'
#dataFile = 'wez_out.csv'#'RandomExperiment_1000_cases__7396_Rad-60_60.csv'

#dataFile = "./Data/Rmax_5000_v3.csv"

AlternateTestData = 'wez_out.csv'
testSplitMode = "RandomSplit" # FixedTestSize / RandomSplit / AlternateTest
dataSplitRatio = 0.30
trainSize = [0]#x for x in range (50,650,50)] #only for alternate
metricsBySize = []
#dataSet = prepareDataFromASA(dataFile, relativeRedHdg=True)
dataSet = prepareDataFromASA(dir + dataFile, relativeRedHdg=False, argumentation = False, size =-1, sinCos = True)#500)
#print(dataSet.describe())
#dataSet = prepareDataFromGodot(dir + dataFile, relativeRedHdg=True)
#dataSet = dataSet[dataSet["maxRange"] != 1]

#dataSet = dataSet.drop([4340, 1304, 940,2190, 3711,2089,4003,2401,2158,218])
X = dataSet.drop(["maxRange"], axis=1)
Y = dataSet.maxRange 


metricsLabel = ["dataType","regressor","interactionsDegree","polyreduction","mae","rmse","R2", "maxError", "fitTime", "predTime", "predictions", "trainSize"]
metricsSumLabel = ["dataType","regressor","interactionsDegree","polyreduction","mae","mae_std","rmse","rmse_std", "fitTime", "fitTime_std","predTime","predTime_std", "trainSize"]
metricsSummary = []

regressorsDict = {1:"MLP", 2:"RBF", 3:"PR", 4:"Linear", 5:"DNN", 6:"LinReg", 7:"ANOVA", 8:"RandomForest"}
regressors = [regressorsDict[6]]#],regressorsDict[6],regressorsDict[1]]

interactionsDegrees = [3]
limitLevel = -1
limitOrder = -1
polRegDegree = 1
reductionsFactors = [-1]#[100]#[100,90,80,70,50,40,30,20,10,5]
folds = 5
printPartial = False
normalizeAll = False

svr_rbf = SVR(kernel="rbf", C=1000, gamma="auto", epsilon=0.1)
svr_lin = SVR(kernel="linear", C=1000, gamma="auto",epsilon=0.1,max_iter=5000000)
svr_poly = SVR(kernel="poly", C=1000, gamma="auto", degree=polRegDegree, epsilon=0.1, max_iter=50000000, coef0=0)
MLP_reg = MLPRegressor(random_state=1, max_iter=500000, activation='tanh',hidden_layer_sizes =(20,20) )
linReg = LinearRegression(n_jobs=(15), fit_intercept=(False))
RF = RandomForestRegressor(max_depth=30)

for regressor in regressors:
    isDNN = False
    for interactionsDegree in interactionsDegrees:
        for polyReductionFactors in  reductionsFactors:
            for tSize in trainSize:   
                
                metricsTest = []
                
                for fold in range(folds):
                    
                    mean_residual = []
                                    
                    if  testSplitMode == "RandomSplit":            
                        X_train, X_test, Y_train, Y_test = sklearn.model_selection.train_test_split(X, Y, test_size = dataSplitRatio, random_state = fold)                        
                    
                    elif testSplitMode == "AlternateTest":                
                        X_train = X[:tSize]
                        Y_train =Y[:tSize]       
                        suffledTest = shuffle(DataSetTest, random_state=fold)
                        X_test = suffledTest.drop(["maxRange"], axis=1)[:600]
                        Y_test = suffledTest.maxRange[:600]
                    
                    elif testSplitMode == "FixedTestSize":
                        X_train, X_test, Y_train, Y_test = sklearn.model_selection.train_test_split(X, Y, test_size = 300,train_size = tSize, random_state = fold)
                    
                    cols = refCols[:len( X_train.columns)] 
                    
                    X_trainS = X_train                    
                    X_testS = X_test                    
                                                                                
                    # Create interaction terms (interaction of each regressor pair + polynomial)
                    #Interaction terms need to be created in both the test and train datasets
                    if interactionsDegree > 0:
                                            
                        
                        interaction = PolynomialFeatures(degree=interactionsDegree, include_bias=False, interaction_only=False)                      
                        X_trainS = pd.DataFrame(interaction.fit_transform(X_trainS), columns=interaction.get_feature_names_out(input_features=list(map(str,list(X_trainS.columns)))))   
                        X_testS = pd.DataFrame(interaction.fit_transform(X_testS), columns=interaction.get_feature_names_out(input_features=list(map(str,list(X_testS.columns)))))
                        cols = X_trainS.columns 
                                                
                    
                    if polRegDegree >= 2 and regressor =="LinReg":                
                        X_trainS = X_trainS.apply(lambda x: x*x )
                        X_testS = X_testS.apply(lambda x: x*x )
                 
                    if limitOrder > 0:
                       
                        for n in range (limitOrder,interactionsDegree+1):
                            X_trainS = X_trainS.drop(X_trainS.filter(regex='\^'+str(n)).columns, axis=1)                        
                            X_testS = X_testS.drop(X_testS.filter(regex='\^'+str(n)).columns, axis=1)                        
                                               
                        cols = X_train.columns                                                    
                                                      
                    
                    if normalizeAll:
                        #scaler = StandardScaler()  
                        scaler = MinMaxScaler()
                        scaler.fit_transform(X_trainS)
                        
                        X_trainS = scaler.transform(X_trainS)    
                        X_testS = scaler.transform(X_testS)                
                        
                        X_trainS = pd.DataFrame(X_trainS)#, columns = cols)    
                        X_testS = pd.DataFrame(X_testS)#,  columns = cols)
                    
                    
                    if regressor == "DNN":
                                    
                        model = computeDnn()
                        isDNN = True
                                         
                    else:
                        
                        if regressor == "PR":
                            model = svr_poly                
                        elif regressor == "RBF":
                            model =  svr_rbf                
                        elif regressor == "Linear":                
                            model = svr_lin
                        elif regressor == "MLP":                
                            model = MLP_reg
                        elif regressor == "LinReg":                
                            model = linReg
                            #model = Pipeline([("polynomial_features", interaction),
                            #     ("linear_regression", linReg)])
                        elif regressor == "ANOVA":
                            # ANOVA SVM-C
                            from sklearn import svm                
                            from sklearn.feature_selection import SelectKBest
                            from sklearn.feature_selection import f_regression
                            from sklearn.pipeline import Pipeline
                            from sklearn.kernel_ridge import KernelRidge
                            
                            #anova_filter = SelectKBest(f_regression, k=20)
                            #clf = svm.SVC(kernel='linear')
                            #model = Pipeline([('anova', anova_filter), ('svc', clf)])
                            # You can set the parameters using the names issued
                            # For instance, fit using a k of 10 in the SelectKBest
                            # and a parameter 'C' of the svm
                            #model.set_params(anova__k=10, svc__C=.1)
                            #model = KernelRidge(kernel="poly",  gamma="auto", degree=polRegDegree,coef0=0)
                            model = KernelRidge(kernel="poly", gamma=0.1)
                        elif regressor == "RandomForest":
                            model = RF
                            
                                      
                        start = time.time()                        
                        model.fit(X_trainS,Y_train)                    
                        fitTime = time.time() - start
                        
                        print(f'\r--------- {regressor} ({fold+1}) / Interaction ({interactionsDegree}) / CorfsRed ({polyReductionFactors})---------------------', end="")
                        
                        #Make new FIT if we are testing coeficients reduction
                        effects = []
                        if polyReductionFactors > 0:
                            
                            coefsAux = ""
                            
                            if regressor == "PR":              
                                coefsAux = [[X_trainS.columns[i],c] for i,c in enumerate(list(model._get_coef()[0]))]                                                     
                                coefsAux = sorted(coefsAux, key=lambda x: -abs(x[1]))
                                #print(coefsAux) 
                            
                            if regressor == "LinReg":
                                coefsAux = [[X_trainS.columns[i],c] for i,c in enumerate(list(model.coef_))]
                                coefsAux = sorted(coefsAux, key=lambda x: -abs(x[1]))
                                #print(coefsAux)         
                            
                            if coefsAux != "":                    
                                insig = [x[0] for x in coefsAux]
                                insig = insig[polyReductionFactors:]  
                                totalCoefs = sum([abs(x[1]) for x in coefsAux])
                                
                                dictEf = {"total":totalCoefs}
                                for x in coefsAux:
                                    dictEf[x[0]] = x[1]/totalCoefs
                                  
                                effects.append(dictEf)          
                                
                                X_trainS = X_trainS.drop(insig, axis=1)
                                X_testS = X_testS.drop(insig, axis=1)
                                  
                                model.fit(X_trainS,Y_train) 
                                
                                coefsAux = ""
                                
                                if regressor == "PR":              
                                    coefsAux = [[X_trainS.columns[i],c] for i,c in enumerate(list(model._get_coef()[0]))]                                                     
                                    coefsAux = sorted(coefsAux, key=lambda x: -abs(x[1]))
                                    #print(coefsAux) 
                                
                                if regressor == "LinReg":
                                    coefsAux = [[X_trainS.columns[i],c] for i,c in enumerate(list(model.coef_))]
                                    coefsAux = sorted(coefsAux, key=lambda x: -abs(x[1]))
                                    #print(coefsAux)        
                                
                                totalCoefs = sum([abs(x[1]) for x in coefsAux])                            
                                dictEf = {"total":totalCoefs}
                                dictEf = {"total":totalCoefs}
                                for x in coefsAux:
                                    dictEf[x[0]] = x[1]/totalCoefs
                                   
                                effects.append(dictEf)
                                                            
                                
                    #metricsTrain.append(evalData("Train Data", regressor, interactionsDegree, polyReductionFactors, model, X_trainS, Y_train, printPartial, True) + [tSize])                             
                    metricsTest.append(evalData("Test Data", regressor,interactionsDegree, polyReductionFactors, model, X_testS, Y_test, printPartial, isDNN)+ [tSize])                
                    if not isDNN:
                        mean_residual.append(Y_test - metricsTest[-1][-2])
                    
                X['resid'] = mean_residual[0]
                metricsDf = pd.DataFrame(metricsTest, columns = metricsLabel)
                metricsDf = metricsDf[metricsDf.trainSize == tSize]
                print("\nTrain Size = ", tSize)    
                print("\nMean MAE:", np.mean(metricsDf.mae),"std:",np.std(metricsDf.mae))
                print("Mean RMSE:", np.mean(metricsDf.rmse),"std:",np.std(metricsDf.rmse))
                print("Max Error:", np.mean(metricsDf.maxError),"std:",np.std(metricsDf.maxError))
                print("Mean R2:", np.mean(metricsDf.R2), "std:",np.std(metricsDf.R2))
                print("Fit  Time:", np.mean(metricsDf.fitTime), "std:",np.std(metricsDf.fitTime))
                print("Pred Time:", np.mean(metricsDf.predTime), "std:",np.std(metricsDf.predTime))
                  
                #summary = ["Test Data", regressor,interactionsDegree, polyReductionFactors, mae, rmse, r2, maxError, fitTime, predTime, y_pred]
                summary = ["TestData", regressor, interactionsDegree, polyReductionFactors,np.mean(metricsDf.mae), np.std(metricsDf.mae), np.mean(metricsDf.rmse),np.std(metricsDf.rmse),
                               np.mean(metricsDf.fitTime),np.std(metricsDf.fitTime),np.mean(metricsDf.predTime),np.std(metricsDf.predTime), tSize]    
                metricsSummary.append(summary)      

if regressor == svr_poly:
    print ("\nPolynomial Coefs = ", len (list(svr_poly._get_coef()[0]))) 

plt.title('Distribution of Residuals WEZ', fontsize=16)
plt.xlabel('Mean Residual', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.5)
plt.hist(mean_residual, bins=20, color='skyblue', edgecolor='black', alpha=0.8)
#plt.xticks(rotation=45)
mean_value = np.mean(mean_residual)
plt.annotate(f'Mean = {mean_value:.2f}', xy=(0.7, 0.9), xycoords='axes fraction', fontsize=12)
plt.figure(figsize=(10, 6))


                                                  
#metricsDf = pd.DataFrame(metrics, columns = metricsLabel)
summaryMetricDf = pd.DataFrame(metricsSummary, columns = metricsSumLabel)
summaryMetricDf.to_csv("Summary" + str(folds) + "_" + tagName +".csv",index=False, header=True, mode='a') 
if (rangeType == "Rmax"):    
    if normalizeAll:
        scalerRmax = scaler    
    interactionsRmax = interaction    
    rmaxModel = model
    
if (rangeType == "Rnez"):    
    if normalizeAll:
        scalerRnez = scaler
    interactionsRnez = interaction
    rnezModel = model
maxIntDegree = interactionsDegrees[-1]

#%%%
#Generate WEZ code for ASA

# Get the powers_ attribute
powers = interactionsRmax.powers_
input_var_names = X_test.columns
# Create a function to generate the monomial term
def monomial_term(powers, input_var_names):
    term = ""
    for i, power in enumerate(powers):
        if power > 0:
            if power == 1:
                term += input_var_names[i] + "*"
            else:
                term += f"{input_var_names[i]}**{power}*"
    return term[:-1]  # Remove the trailing '*'

# Define the input variable names
#input_var_names = ['x1', 'x2']
# Get the coefficients (weights) from the linear regression model
weights = model.coef_

# Define the input variable names

# Generate the weighted polynomial expression
weighted_polynomial_expression = ""
for i, powers_row in enumerate(interactionsRmax.powers_):
    weight = weights[i]
    term = monomial_term(powers_row, input_var_names)
    if term != "1":  # Skip the constant term
        weighted_polynomial_expression += f"{weight}*{term} + "

# Remove the trailing ' + '
weighted_polynomial_expression = weighted_polynomial_expression[:-3]

print("Weighted Polynomial Expression:", weighted_polynomial_expression)


#%%%
metricBySizeDf = pd.DataFrame(metricsBySize, columns = ["model", "trainSize", "MAE", "StDev"])

metricBySizeDf.to_csv("metric_Train_size.csv",mode='a',index=False)

x = metricBySizeDf.trainSize
y = metricBySizeDf.MAE
e = metricBySizeDf.StDev

plt.errorbar(x, y, yerr = e, fmt='-o')
plt.show()


#%%% EFFECTS
idEf =1
tot = 0

for i,e in enumerate(effects[idEf]):
    if e == 'total':
        continue
    print(i , e, effects[idEf][e])
    tot = tot + abs(effects[idEf][e])
    if i >= 200:
        break
print(tot)   

    
#%%%#HEAT MAP
import seaborn as sns

import matplotlib.pyplot as plt

corrData =  dataSet.iloc[:,:10]
corrData['maxRange'] = dataSet['maxRange'] 
correlation_mat = corrData.corr()
sns.heatmap(correlation_mat, annot = True)
plt.show()



#%%% Create Plot for Specific Cases


#cases = [ 0, -5000*utils.feet2m, 5000*utils.feet2m]
#cases = [ -10000, -20000, 0, 10000, 20000]
cases = [10000, 20000,30000,40000,50000]
aspect    =  -180    /180*pi
angle_off = 60  /180*pi

colors = ['b','g', 'r', 'y', 'm', 'b']

xRad = [x/10 for x in range(-600,600,1)]

testCaseRef = pd.DataFrame(xRad, columns=["radials"])

fig, (ax1)= plt.subplots(1, 1,  gridspec_kw={'height_ratios': [3]}, figsize=(8, 8), dpi=300 )
fig.subplots_adjust(wspace=0, hspace=0.4)
ax = plt.subplot(1, 1, 1, projection='polar')
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1) 

preds = []
for i,caseS in enumerate(cases):
    
    #dataDf = fulldataDf[['BL_Speed', 'RD_Speed', 'rad', 'RD_Hdg', 'BL_Alt', 'RD_Alt']]        
    testCase = testCaseRef.copy()
    testCase['blue_alt'] = caseS / 150000
    testCase['diffAlt'] = caseS  / 150000#caseS#5000#testCase['BL_Alt'] - 5632
            
    testCase['aspect'] = testCase['radials'] 
    testCase['cosAspect'] = testCase.apply(lambda x: math.cos(x.aspect*math.pi/180), axis=1)
    testCase['sinAspect'] = testCase.apply(lambda x: math.sin(x.aspect*math.pi/180), axis=1)     
    
    testCase['angle_off'] = testCase['radials'] + 0
    testCase['cosAngleOff']= testCase.apply(lambda x: math.cos(x.angle_off*math.pi/180), axis=1)
    testCase['sinAngleOff'] = testCase.apply(lambda x: math.sin(x.angle_off*math.pi/180), axis=1)     
    
        
        
    
    testCase = testCase.drop(['aspect'], axis=1)              
    testCase = testCase.drop(['radials'], axis=1)   
    testCase = testCase.drop(['angle_off'], axis=1)
    
    #print(testCase.describe())
    interactionSpc = PolynomialFeatures(degree=4, include_bias=False, interaction_only=False)
    testCase = pd.DataFrame(interactionSpc.fit_transform(testCase), columns=interactionSpc.get_feature_names_out(input_features=list(map(str,list(testCase.columns)))))
    #scaler = StandardScaler()  
    #scaler = MinMaxScaler()
    #testCase = scaler.transform(testCase) 
    #testCase = pd.DataFrame(testCase)
          
    
    predCase = model.predict(testCase) 
    preds.append(predCase)
    
    
    #ax.scatter(xRad, predCase, marker='.', s = 5 )#, color=[("b" if x == 2 else ("r" if x==1 else "g")) for x in cMap])
    ax.scatter(list(map(lambda x: x * math.pi/180, xRad)), predCase, marker='.', s = 2, c = colors[i], label=caseS )#, color=[("b" if x == 2 else ("r" if x==1 else "g")) for x in cMap])
    ax.set_rmax(55)
    ax.set_rmin(0)
    
ax.set_thetamin(-60)
ax.set_thetamax(60)
ax.legend(prop={'size': 9}, frameon=True, ncol=3, loc="lower center", markerscale=3,fontsize=10)
ax.grid( color = "gray",linestyle='--', linewidth=0.5, alpha=0.5 )     
ax.set_rmin(0)
#plt.scatter(xRad, predCase)    


# %%

alt_blue = 50000
diff = 25000
aspect    =  0  /180*pi
angle_off = 180 /180*pi

testCase = pd.DataFrame( 
                        {'blue_alt': [alt_blue/150000], 
                         'diffAlt': [diff/150000], 
                         'cosAspect' : math.cos(aspect),
                         'sinAspect':  math.sin(aspect),
                         'cosAngleOff': math.cos(angle_off),
                         'sinAngleOff':  math.sin(angle_off)})


print(testCase)
interactionSpc = PolynomialFeatures(degree=4, include_bias=False, interaction_only=False)
testCase = pd.DataFrame(interactionSpc.fit_transform(testCase), columns=interactionSpc.get_feature_names_out(input_features=list(map(str,list(testCase.columns)))))
    #scaler = StandardScaler()  


#testCase = pd.DataFrame(test)
predCase = model.predict(testCase) 

print(predCase)
# %%
