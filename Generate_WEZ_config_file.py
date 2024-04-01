# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 23:32:25 2022

@author: ieav-asa
"""
#def generateWezConfigFile(name, scalerRmax, interactionsRmax, rmaxModel, scalerRnez, interactionsRnez, rnezModel, maxIntDegree):
def generateWezConfigFile(name, scalerRmax, interactionsRmax, rmaxModel, scalerRnez, maxIntDegree):

              
    listCoefsRmax = list(rmaxModel.coef_)
    #listCoefsRnez = list(rnezModel.coef_)
    print(listCoefsRmax)
    
    # print(len(listCoefsRmax))
    # print(scalerRmax.n_features_in_)   
    # print(scalerRmax.data_min_)
    # print(scalerRmax.data_max_)
    # print(listCoefsRmax)
    
    # print(getMinMaxCoefs(interactionsRmax,maxIntDegree ))    
    print(interactionsRmax)
    # f_cpp = open(name + ".cpp", "w")
    # f_cpp.write(wezCpp)
    # f_cpp.close()
    
    # f_templateH = open('WezAsa_template_header.txt', "r")
    # WezH = f_templateH.read()
    
    # while WezH.find('$name') != -1:
    #     WezH = WezH.replace('$name', name)
    
    # f_h = open(name + ".h", "w")
    # f_h.write(WezH)
    # f_h.close()

def getMinMaxCoefs(interaction, maxIntDegree):
    vidx = []
    exps = []     
    for i in interaction.powers_:
        aux_vidx = []
        aux_exps = []
        for idx,k in enumerate(i):
            if k != 0:
               aux_vidx.append(idx+1) 
               aux_exps.append(k)
    
        while len(aux_vidx) < maxIntDegree:
            aux_vidx.append(0) 
            aux_exps.append(0)
                   
        vidx.append(aux_vidx)   
        exps.append(aux_exps)
    
    line_vidx = []
    line_exps = []
    for i in range(maxIntDegree):
        line_vidx.append([x[i] for x in vidx] )
        line_exps.append([x[i] for x in exps] )
        
    return [line_vidx, line_exps]