#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 16:39:32 2023

@author: Daniel Bunzendahl
"""

try:

    import pandas as pd
    import locale
    import numpy as np
    import os
    import matplotlib.pyplot as plt
    import time
    from rich.progress import track
    import multiprocessing as mp
    import logging
    import threading
    from multiprocessing.pool import Pool
    from time import sleep
    import json
    from alive_progress import alive_bar
    import sys
    import warnings

    locale.setlocale(locale.LC_ALL, 'nl_NL')

    myCtes = pd.DataFrame( columns= ['filename','section','maxDeltaL','kelvin','maxL0','cte','temperature'])

    pass
except Exception as e:
    print("****************************")
    print("** INSTALLATION-ANLEITUNG **")
    print("** ---------------------- **")
    print("** Auszuführender Befehl: **")
    print("")
    print("python3 -m pip install pandas numpy matplotlib rich alive_progress openpyxl warnings")
    print("")
    print("")
    print("")
    print("... einfach kopieren, einfügen und Enter...)")
    print("")
    print("")
    raise

def readAramisSectionFile(filename):
    """
    Reads Section-Export of Aramis line by line and seperate cols by double spaces as convert values to float 

    Args:
        filename (STRING): Filename of an Aramis Section Export (e.g x1v1_section0_0-1.txt)

    Returns:
        measurementDataFrame (OBJECT): Found Measurements as Pandas Dataframe with columns ['index','l0','deltaL','genulltesDeltaL'].

    """
    lines= []
    measurementDataFrame = pd.DataFrame(columns=['index','l0','deltaL','genulltesDeltaL'])
    file = open(filename)
    for line in file:
        # stripping each line into a list
       line = line.rstrip() 
       lines.append(line)
    file.close()
    length = len(lines)
    i=1
    # converting values decimal sign from comma to dot 
    while i <= length - 1:
        a = lines[i].split("  ")
        #measurementDataFrame.loc[i] ={'index':i,'l0':locale.atof(a[0]), 'deltaL':locale.atof(a[1])}
        measurementDataFrame.loc[i] ={'l0':locale.atof(a[0]), 'deltaL':locale.atof(a[1])}
        i += 1
    logging.debug("return readAramisFile",measurementDataFrame)
    return measurementDataFrame

def getMinDeltaL(data):
    #if not negativ ...
    min = data.min()
    return min 

def findMinDeltaL(data):
    """
    Calculates the minimal of all DeltaL in data

    Args:
        data (OBJECT): All DeltaL in DataFrame.

    Returns:
        minDeltaL (FLOAT): The lowes DeltaL found.

    """
    minDeltaL = data.min()
    return minDeltaL

    
def nullingAllData(data):

    """
    Generates a only positive coll of sections deltaL by finding the minimum and add this to become the lowest value to be zero
    This method is not used currently and was developed while finding a good solution.
    Args:
        data (OBJECT): All Data in one DataFrame.

    Returns:
        data (OBJECT): All Data with additional filled 'genulltesDeltaL'

    """
    # Step 1: find minimal DeltaL
    minDeltaL = data["deltaL"].min()
    #minLength = data['l0'].min()
   
    for l in data['deltaL']:
        if l < 0:
            print("data (-): ",l)
            data.loc[l, 'genulltesDeltaL'] = round(l-minDeltaL,6)
            print("round(l-minDeltaL,6)",round(l-minDeltaL,6))
        else:
            print("data (+): ",l)
            data.loc[l, 'genulltesDeltaL'] = round(l-minDeltaL,6)
    return data

def nullingDeltaL(data):
    """
    Nulling of DeltaL by checking if it is negative and if so calculate a positiv bias

    Args:
        data (OBJECT): Sections DeltaL of given Measurments.

    Returns:
        nulledDeltaL (OBJECT): Nulled DeltaL values as Pandas DataFrame ["deltaL"].

    """
    
    # Step 1: find minimal DeltaL
    minDeltaL = findMinDeltaL(data["deltaL"])
    
    # Step 2: check DeltaL is negativ and round to 6 decimal
    
    if minDeltaL < 0:
        for l in data["deltaL"]:
            data.loc[l,'genulltesDeltaL'] = round(l-minDeltaL, 6)
    else:
        for l in data["deltaL"]:
            data.loc[l,'genulltesDeltaL'] = l
    
    nulledDeltaL = data
    return nulledDeltaL

def findMaxDeltaL(data):
    """
    Finds the maximal DeltaL corresponding to the full length of L0

    Args:
        data (OBJECT): Pandas DataFrame containing all DeltaL.

    Returns:
        maxDeltaL (FLOAT): The value of the maximum DeltaL.

    """
    maxDeltaL = data.max()
    return maxDeltaL

def getMaxDeltaL(data):
    
    maxDeltaL = data.max()
    
    return maxDeltaL

def findMaxL0(data):
    """
    Find the maximum length of L0

    Args:
        data (OBJECT): Pandas DataFrame with ["l0"].

    Returns:
        maxL0 (FLOAT): The maximum l0.

    """
    maxL0 = data.max()
    return maxL0

def getMaxL0(data):
    maxL0 = data.max()
    return maxL0


def getCTE(deltaL,kelvin, maxL0, stage):
    #print("deltaL/kelvin*maxL0: ",deltaL,kelvin,maxL0)
    if kelvin == 0:
        return 0
    else:
        #cte = deltaL/(kelvin*maxL0)
        cte = deltaL/(kelvin*maxL0)
        return cte

def getCTEInterStageSquare(deltaL,kelvin, l, stage):
    #print("deltaL/kelvin*l: ",deltaL,kelvin,l)

    if l == 0.0 or kelvin == 0:
        return 0
    else:
        #cte = deltaL/(kelvin*maxL0)
        cte = abs(deltaL)/(kelvin*l)
        #cte = deltaL/(kelvin*l)
        logging.debug("Differential CTE of square: %s" % cte)
        return cte

def parallelCalculatingCTE(parameters):
    """
    Parallelizing what can be done in parallel with Aramis Exports to get out a table of reasonable data for CTE calculation
    The logging.debug() is only for sequenziell processing and not in asynchronouse mode due to not working without flash
    Args:
        parameters (OBJECT): path, filename, temperature, section, stage, absMaxL0, excelFileName, experimentNumber

    Returns:
        dataset (OBJECT): Pandas DataFrame with 7 columns of STRINGs ['experimentsNumber','filename','section','maxDeltaL','kelvin','maxL0','cte','temperature','absMaxL0','path','exceldatei']
        
    """
    
    os.chdir(parameters["path"])
    filename = parameters["filename"]
    temperatureOfFilename = parameters["temperature"]
    section = parameters["section"]
    stage = parameters["stage"]
    absMaxL0 = parameters["absMaxL0"]
    excelFileName = parameters["excelFileName"]
    experimentsNumber = parameters['experimentsNumber']
    diffCTE = parameters['diffCTE']
    pid = os.getpid()
    logging.debug("pid: %s" % pid )
    
    # Step 1: read Aramis Section file into Pandas DataFrame ['index','l0','deltaL','genulltesDeltaL']
    tableOfMeasurements = readAramisSectionFile(filename)
    logging.debug("Filename %s reading done" % filename )
   
    # Step 2a: Calculate differential CTE to compare
    
    calculatedInterStageSquareCTE = []
    measurments = tableOfMeasurements.to_numpy()
    for line in measurments:
        rowsDeltaL = line[2]
        rowsL = line[1]
        calculatedInterStageSquareCTE.append(round(getCTEInterStageSquare(rowsDeltaL,(temperatureOfFilename-30),rowsL, stage)*1000000,6))
    # https://blog.finxter.com/numpy-runtimewarning-mean-of-empty-slice/
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        interStageCTE = round(np.nanmean(calculatedInterStageSquareCTE),6)
    logging.debug("interStageCTE : %s" % interStageCTE)
    
    # Step 2b: Nulling of DeltaL
    nulled = nullingDeltaL(tableOfMeasurements)
    logging.debug("Section %s nulling done" % section)
    
    # Step 3: Find maxL0
    maxL0 = findMaxL0(tableOfMeasurements['l0'])
    logging.debug("Maximal L0 found at %s mm" % maxL0 )

    # Step 4: Find maxDeltaL
    maxDeltaL = findMaxDeltaL(nulled["genulltesDeltaL"])
    logging.debug("Maximal Delta L found at %s mm" % maxDeltaL )

    # Step 5: Calculate CTE in form of 10^-6 and rounded to 6 decimals
    calculatedCTE = round(getCTE(maxDeltaL,(temperatureOfFilename-30),absMaxL0, stage)*1000000,6)
    logging.debug("CTE %s" % calculatedCTE )
    logging.debug("Calculated CTE: %s" % calculatedCTE)

    # Step 6: Build everything together into a list
    # should stay a flat array due to this has to be feeded into sheduling in parallel. experimentsNumber is for getting things together by iterating over that parameter
    dataset = {'experimentsNumber':experimentsNumber,'filename': filename,'section': section,'maxDeltaL':maxDeltaL,'kelvin':(temperatureOfFilename-30),'maxL0':maxL0,'cte':calculatedCTE,'diffCTE':diffCTE,'interStageCTE':interStageCTE,'temperature':temperatureOfFilename, 'absMaxL0':absMaxL0, 'stage':parameters["stage"], 'path':parameters["path"], 'experiment': parameters["switch_sample"], 'excelFileName': excelFileName}
    logging.debug("dataset %s:" % dataset)

    sys.stdout.write(".")
    sys.stdout.flush()
    return dataset

def generateCTE_SheetFromRawMeasurements(sections, temperatures):
    """
    Constructs filenames from sections, creates a dataframe and calls other functions for creating CTEs

    Args:
        sections (LIST): Keys are Aramis-Sectionnumbers and corresponding manuell naming as values are part of filenames (eg. {12: 'x1vCu', 13: 'x2vCu', ... 29: 'y3vCu'}).
        temperatures (LIST): Keys are Aramis-Section-hirarchiestrings corresponding with absolut temperatures in °C as values (e.g. {'_0-0': 30, '_0-1': 50, '_0-2': 50, ... '_0-19': 230, '_0-20': 230}).

    Returns:
        false (BOOLEON): if filename not found in current directory
        names (OBJECT): Pandas DataFrame with 7 columns of STRINGs ['filename','section','maxDeltaL','kelvin','maxL0','cte','temperature']

    """
    count = 0
    extension = "txt"
    sec = "_section" # all Aramis Sections contain this sting in filenames
    names = pd.DataFrame(columns= ['filename','section','temperature','stage','absMaxL0'])
    path = os.getcwd()
    for key in sections:
        s = sections[key]
        for t in temperatures:
            filename = sections[key]+str(sec)+str(key)+str(t)+"."+str(extension) # e.g x1v1_section0_0-1.txt
            if os.path.isfile(filename):
                stage = t.split('-')
                names.loc[count] = {'filename': filename,'section': s,'temperature':temperatures[t], 'stage': stage[1] ,'absMaxL0': False, 'path':path }
                count +=1
            else:
                logging.warning("not found:", filename)
                return False    
    return names

if __name__ == '__main__':
    logging.info("Installation erfolgreich überprüft... [X]")
    # Using Logging the best way https://codegree.de/python-logging/
    logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)
    NUM_WORKERS = 40
    mp.freeze_support()
    # Prevenht warnings about non using .loc[..] ttps://statologie.de/setting-with-copy-warning-pandas/
    pd.options.mode.chained_assignment = None
    currentPath = os.getcwd()
    
    # Das Programm geht davon aus, dass je Probe 3 X-Sections und 3 Y-Sections als separate Dateien vorliegen
    '''
    Das Programm geht von 3 X-Sections und 3 Y-Sections je Versuchsträger aus.
    Die Versuchsträger sind mit v1, v2 und v3 unterschieden.
    Die Sections sind mit x1, x2, x3, y1, y2, y3 unterschieden.
    Daraus bildet sich der Dateiname (z.B. y3v2) mit der vom Aramis vorgegebenen Sectionsnamen (_section11)
    sowie der Benennung der Stages (_0-11.txt).
    Format: 
    '''
    # Stages entsprechen folgender Temperatur
    start = time.time()
    temperatureOfStages = {'_0-0': 30, '_0-1': 50, '_0-2': 50, '_0-3': 70, '_0-4': 70, '_0-5': 90, '_0-6': 90, '_0-7': 110, '_0-8': 110, '_0-9': 130, '_0-10': 130, '_0-11': 150, '_0-12': 150, '_0-13': 170, '_0-14': 170, '_0-15': 190, '_0-16': 190, '_0-17': 210, '_0-18': 210, '_0-19': 230, '_0-20': 230} 
    sections_vCu = {12: 'x1vCu', 13: 'x2vCu', 14: 'x3vCu', 27: 'y1vCu', 28: 'y2vCu', 29: 'y3vCu'}
    sections_vNo = {9: 'x1vNo', 10: 'x2vNo', 11: 'x3vNo', 24: 'y1vNo', 25: 'y2vNo', 26: 'y3vNo'}
    sections_v1_150 = {0: 'x1v1', 1: 'x2v1', 2: 'x3v1', 15: 'y1v1', 16: 'y2v1', 17: 'y3v1'}
    sections_v2_150 = {3: 'x1v2', 4: 'x2v2', 5: 'x3v2', 18: 'y1v2', 19: 'y2v2', 20: 'y3v2'}
    sections_v3_150 = {6: 'x1v3', 7: 'x2v3', 8: 'x3v3', 21: 'y1v3', 22: 'y2v3', 23: 'y3v3'}
    sections_v1_180 = {0: 'x1v1', 1: 'x2v1', 2: 'x3v1', 9: 'y1v1', 10: 'y2v1', 11: 'y3v1'}
    sections_v2_180 = {3: 'x1v2', 4: 'x2v2', 5: 'x3v2', 12: 'y1v2', 13: 'y2v2', 14: 'y3v2'}
    sections_v3_180 = {6: 'x1v3', 7: 'x2v3', 8: 'x3v3', 15: 'y1v3', 16: 'y2v3', 17: 'y3v3'}

    pathOfVersions = {0: currentPath+r'/tests/vCo_TestMovementCorrected',
                      1: currentPath+r'/tests/vNo_TestMovementCorrected',
                      2: currentPath+r'/tests/v1_150C_MovementCorrected',
                      3: currentPath+r'/tests/v2_150C_MovementCorrected',
                      4: currentPath+r'/tests/v3_150C_MovementCorrected',
                      5: currentPath+r'/tests/v1_180C_MovementCorrected',
                      6: currentPath+r'/tests/v2_180C_MovementCorrected',
                      7: currentPath+r'/tests/v3_180C_MovementCorrected',
                     # 0: currentPath+r'/tests/v1_150C_MovementCorrected',
                     # 0: currentPath+r'/tests/vCo_TestMovementCorrected',

    }
    switch_sample = {
        0: sections_vCu,
        1: sections_vNo,
        2: sections_v1_150,
        3: sections_v2_150,
        4: sections_v3_150,
        5: sections_v1_180,
        6: sections_v2_180,
        7: sections_v3_180
        #0: sections_vCu
    }
    excelFileNames ={
        0: "Kupfer_MovementCorrected",
        1: "noParam_MovementCorrected",
        2: "v1_150C_MovementCorrected",
        3: "v2_150C_MovementCorrected",
        4: "v3_150C_MovementCorrected",
        5: "v1_180C_MovementCorrected",
        6: "v2_180C_MovementCorrected",
        7: "v3_180C_MovementCorrected",
        #0: "Kupfer_TestMovementCorrected",
        }
    numberOfExperiments = len(excelFileNames)
    numberOfStages = 21
    numberOfSections= 6
    absMaxL0 = 0
    filenamesMaxL0 = []
    
    names = pd.DataFrame(columns= ['filename','section','temperature','stage','absMaxL0'])
    experiments = 0
    testMode = False
    if testMode:
        numberOfExperiments = 1
    print("Anzahl Experimente: ",numberOfExperiments)

    allStepsToGo = numberOfExperiments*numberOfSections*numberOfStages
    global countFiles
    countFiles = 0;
    #https://github.com/rsalmei/alive-progress
    with alive_bar(allStepsToGo) as bar:
        
        while experiments < (numberOfExperiments): #or each experiment (11) # 0-10
            
            bar.title("Experiment %s" % excelFileNames[experiments])
            currentPath = os.getcwd()
            path =pathOfVersions.get(experiments)
            os.chdir(path)
            sectionList = switch_sample.get(experiments)
            excelFile = excelFileNames.get(experiments)
            
            names = generateCTE_SheetFromRawMeasurements(sectionList, temperatureOfStages)
            logging.debug("len Names",names)
            sec = 0
            nameListCount = numberOfSections * numberOfStages # 6 Sections * 21 Stages
            experimentsMeasurementNumber = 0
            while sec < (numberOfSections):#for each section (6) # specific keys given from Aramis
                stage = 0
                absMaxL0 = 0
                sectionLengthOfSqares =[]
                while stage < (numberOfStages):
                    diffCTELocal = 0
                    stageFilename = names["filename"].loc[experimentsMeasurementNumber]
                    temperature = names["temperature"].loc[experimentsMeasurementNumber]
                    tableOfMeasurements = readAramisSectionFile(stageFilename)
                    logging.debug("Filname %s of Experiment %s" % (stageFilename, experiments))
                    
                    if stage == 0:                    
                        absMaxL0 = findMaxL0(tableOfMeasurements['l0'])
                        for l in tableOfMeasurements['l0']:
                            sectionLengthOfSqares.append(l)
                    else:
                        alphas = []
                        i = 0
                        for l in tableOfMeasurements['l0']:
                            deltaLOfSqare = l-sectionLengthOfSqares[i]
                            if sectionLengthOfSqares[i] != 0.0:
                                alphas.append(deltaLOfSqare/((temperature-20)*sectionLengthOfSqares[i]))
                            i+=1
                        # https://blog.finxter.com/numpy-runtimewarning-mean-of-empty-slice/
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", category=RuntimeWarning)
                            diffCTELocal = round(np.nanmean(alphas)*1000000,6)
                        #print(diffCTELocal)


                    experimentsValues = names.loc[experimentsMeasurementNumber]
                    experimentsValues["absMaxL0"] = absMaxL0
                    experimentsValues['filename'] = stageFilename
                    experimentsValues['switch_sample'] = int(experiments)
                    experimentsValues['section']= sec
                    experimentsValues['temperature']=temperature
                    experimentsValues['absMaxL0']= absMaxL0
                    experimentsValues['stage']= stage
                    experimentsValues['path']=path
                    experimentsValues['diffCTE']=diffCTELocal
                    experimentsValues['excelFileName'] = excelFile
                    experimentsValues['experimentsNumber'] = int(experiments)
                    filenamesMaxL0.append(experimentsValues)
                    stage+=1
                    experimentsMeasurementNumber+=1
                    bar()
                sec+=1
            
            os.chdir(currentPath)
            experiments+=1
            
    logging.info("List of generated jobs to be processes for getting CTEs: %s " % filenamesMaxL0)
    end = time.time()
    zeit = end - start
    logging.info("Berechnungsdauer in Sekunden: %s " %(zeit))
    if testMode:
        parallelCalculatingCTE(filenamesMaxL0[0])
        sys.exit(0)
    startPoolTimer = time.time()
    with Pool(processes=4) as pool:
        
        result = pool.map_async(parallelCalculatingCTE, filenamesMaxL0, chunksize=5)#, callback=safeExcel)
        result.wait()
        print("all done!")
        endPoolTimer = time.time()
        asyncZeit = endPoolTimer-startPoolTimer
        print("Sequenzielle Berechnungsdauer in Sekunden:  " ,(zeit))
        print("Asynchrone Berechnungsdauer in Sekunden:  " ,(asyncZeit))


        # check if the tasks are complete
        if result.ready():
            logging.info('Tasks are complete')
            value =result.get()
            logging.info("results: ",value)
            
            files = []
            for r in range(len(excelFileNames)):
                files.append([])
                
            for dataset in value:
                files[int(dataset["experimentsNumber"])].append(dataset)
                
            i = 0
            currentPath = os.getcwd()
            for file in files:
                # Howto https://draeger-it.blog/erstellen-von-excel-mappen-mit-python3-und-xlsxwriter/
                c = pd.DataFrame(file)#cte
                c.to_excel('CTEs_'+excelFileNames[i]+'.xlsx', sheet_name=excelFileNames[i])
                logging.debug("Sheet happens in: %s" % currentPath)
                logging.info('CTEs_'+excelFileNames[i]+'.xlsx')
                i+=1
            
        else:
            print('Tasks are not complete')
        # close the process pool
        pool.close()
        # wait for all tasks to complete
        pool.join()
