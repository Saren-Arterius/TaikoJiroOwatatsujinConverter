#!/usr/bin/python3.3
import re
import sys

global fumenDict, newline, lastLegnth, BalPos, unit_str, legnth, firstLine

def getInfo():
    tjaInfoDic = {}
    tjaInfoList = tjaFile.split("\n")
    for line in tjaInfoList:
        list = line.split(":")
        if (len(list) == 2):
            key, val = list
            if (key == "BALLOON"):
                val = val.split(",")
                tjaInfoDic[key] = val
            if (key == "COURSE" and val.lower() == "oni"):
                tjaInfoDic[key] = 3
            else:
                tjaInfoDic[key] = val
    return tjaInfoDic

def fileOpen():
    if (len(sys.argv) == 1):
        print('未指定TJA檔案\nTJA file not specified.')
        input()
        raise Exception('TJA file not specified.') 
    with open(sys.argv[1], "rt") as tjaFile:
        try:
            tjaFile = re.sub("\r", "", tjaFile.read())
        except UnicodeDecodeError:
            print('TJA含有亂碼，請移除TITLE和SUBTITLE的內容\nYour TJA file contains character that cannot be decoded. Please remove any content of TITLE and SUBTITLE')
            input()
            sys.exit()
    if ((tjaFile.find("#START")) == -1):
        print('TJA格式錯誤, TJA檔案內不含"#START"\nTJA file does not include "#START"')
        input()
        raise Exception('TJA File does not include "#START"') 
    elif ((tjaFile.find("#END")) == -1):
        print('TJA格式錯誤, TJA檔案內不含"#END"\nTJA file does not include "#END"')
        input()
        raise Exception('TJA file does not include "#END"')
    return tjaFile

def infoWrite():
    output.write("head=owata1\n&format=1")
    output.write("\n&title="+tjaInfoDic["TITLE"])
    if ("SONGVOL" in tjaInfoDic):
        output.write("\n&bgm_vol="+tjaInfoDic["SONGVOL"])
    if ("SEVOL" in tjaInfoDic):
        output.write("\n&se_vol="+tjaInfoDic["SEVOL"])
    if ("COURSE" and "LEVEL" in tjaInfoDic):
        output.write("\n&level"+str((int(tjaInfoDic["COURSE"])+1))+"="+tjaInfoDic["LEVEL"])
    else:
        print('TJA格式錯誤, TJA檔案內不含COURSE或LEVEL\nTJA File does not include "COURSE" nor "LEVEL"')
        input()
        raise Exception('TJA File does not include "COURSE" nor "LEVEL"')
    if ("OFFSET" in tjaInfoDic):
        output.write("\n&start_time="+str(float(tjaInfoDic["OFFSET"])*-1))
    if ("BPM" in tjaInfoDic):
        output.write("\n&unit_time="+str(60/float(tjaInfoDic["BPM"])/4))
        output.write("\n&scroll_time="+str(60/float(tjaInfoDic["BPM"])))
    if ("SCOREINIT" in tjaInfoDic):
        output.write("\n&score"+str(int(tjaInfoDic["COURSE"])+1)+"="+tjaInfoDic["SCOREINIT"]+","+tjaInfoDic["SCOREDIFF"])
    output.write("\n&bunki=0,0,0,0\n&seq"+str(int(tjaInfoDic["COURSE"])+1)+"=")

def fumenComment():
    global lastUnitT, unit_str
    if (line == "#GOGOSTART"):
        newline.append("gg")
    elif (line == "#GOGOEND"):
        newline.append("g")
    elif (line.startswith("#BPMCHANGE")):
        fumenDict["BPM"] = float(re.sub("^[^\d.-]+", "", line))
        unit_time = (60/fumenDict["BPM"])/(legnth/4)*fumenDict["MEA"]
        unit_str = "u("+str(unit_time)+")"
        print("#BPMCHANGE",unit_str)
        if (unit_time != lastUnitT):
            newline.insert(0,unit_str)
            lastUnitT = unit_time
        fumenDict["SCRisChanged"] = True
    elif (line.startswith("#SCROLL")):
        fumenDict["SCRfac"] = float(re.sub("^[^\d.-]+", "", line))
        fumenDict["SCRisChanged"] = True
    elif (line.startswith("#MEASURE")):
        fumenDict["MEA"] = float(eval(re.sub("^[^\d/]+", "", line)))
    elif (line.startswith("#DELAY")):
        fumenDict["DEL"] = float(re.sub("^[^\d.-]+", "", line))
        DEL_str = "u("+str(fumenDict["DEL"])+"),"
        newline.append(DEL_str)
        lastUnitT = fumenDict["DEL"]
        fumenDict["BPMisChanged"] = True
    elif (line == "#BARLINEON"):
        fumenDict["BARLINEON"] = True
    elif (line == "#BARLINEOFF"):
        fumenDict["BARLINEON"] = False
    elif (line.startswith("#END")):
        print("轉換完成! 按任意鍵退出. \nFile converted! Press any key to exit.")
        input()
        sys.exit()
    unitTimeChange()
    scrollTimeChange()
    return fumenDict
        
def noteConvert(line):
    global BalPos
    line = re.sub(r"0", ",", line)
    line = re.sub(r"1", "1,", line)
    line = re.sub(r"2", "2,", line)
    line = re.sub(r"3", "3,", line)
    line = re.sub(r"4", "4,", line)
    line = re.sub(r"5", "55,", line)
    line = re.sub(r"6", "66,", line)
    line = re.sub(r"8", "56,", line)
    BalloonsInALine = len(re.findall(r"7", line))
    if (BalloonsInALine >= 1):
        if ("BALLOON" in tjaInfoDic):
            for i in range(0,BalloonsInALine):
                line = re.sub(r"7", "77("+tjaInfoDic["BALLOON"][BalPos]+"),", line, 1)
                BalPos = BalPos+1
        else:
            print('TJA格式錯誤, TJA譜面內有氣球但沒有"BALLOON"\nFumen contains balloon but TJA file lacks "BALLOON"')
            input()
            raise Exception('Fumen contains balloon but TJA file lacks "BALLOON"')
    line = re.sub(r"56,", "567,", line)
    return line

def unitTimeChange():
    global lastUnitT, unit_str, lastLegnth, legnth
    if ((legnth != fumenDict["MEA"]*16) and (legnth != 0)) or (fumenDict["BPMisChanged"] == True) or (legnth != lastLegnth and (lastLegnth != 0) and (legnth != 0)):
        unit_time = (60/fumenDict["BPM"])/(legnth/4)*fumenDict["MEA"]
        if (unit_time != lastUnitT):
            unit_str = "u("+str(unit_time)+")"
            if (fumenDict["BPMisChanged"]):
                newline.append(unit_str)
            else:
                newline.insert(0,unit_str)
            lastUnitT = unit_time
        fumenDict["BPMisChanged"] = False
        
def scrollTimeChange():
    global lastScrT, SCR_time
    if ((fumenDict["SCRisChanged"] == True)):
        SCR_time = (60/fumenDict["BPM"])/fumenDict["SCRfac"]
        if (lastScrT != SCR_time):
            SCR_str = "s("+str(SCR_time)+")"
            newline.insert(0,SCR_str)
        fumenDict["SCRisChanged"] == False
    lastScrT = SCR_time

tjaFile = fileOpen()
output = open(sys.argv[1]+".data.txt", 'w+')
tjaParted = tjaFile.partition("#START")
tjaInfoDic = getInfo()
infoWrite()
tjaFumen = re.split(',', re.sub("\n+", "\n", tjaParted[2]))
fumenDict = {}
fumenDict["BPM"],fumenDict["SCRfac"],fumenDict["MEA"],fumenDict["BARLINEON"],newline,lastLegnth,BalPos,lastUnitT,lastScrT,SCR_time = float(tjaInfoDic["BPM"]),float(1),float(1),True,[],0,0,0,0,0
for line in tjaFumen:
    legnth,fumenDict["BPMisChanged"],fumenDict["SCRisChanged"],firstLine,fumenDict["DEL"] = 0,False,False,True,0
    line = re.split('\n', line)
    del line[0]
    for seq in line:
        if (seq and (not seq.startswith("#"))):
            legnth = (len(seq)) + legnth
    for line in line:
        if (line.startswith("#")):
            fumenDict = fumenComment()
        elif (line):
            line = noteConvert(line)
            newline.append(line)
            unitTimeChange()
            lastLegnth = legnth
        else:
            unit_time = ((60/fumenDict["BPM"])/(legnth/4))*legnth
            unit_str = "u("+str(unit_time)+"),"
            newline.append(unit_str)
            lastUnitT = unit_time
            fumenDict["BPMisChanged"] = True
    for line in newline:
        if ((fumenDict["BARLINEON"] == True) and (firstLine == True)):
            if (line[0] == ","):
                output.write('\n' + line[:0] + '|' + line[0:])
                firstLine = False
            elif ((line[0] == "7") and (line[1] == "7")):
                output.write('\n' + line[:2] + '|' + line[2:])
                firstLine = False
            elif (re.match("\d", line[0])):
                output.write('\n' + line[:1] + '|' + line[1:])
                firstLine = False
            else:
                output.write('\n' + line)
        else:
            if (line):
                output.write('\n' + line)
    newline = []
