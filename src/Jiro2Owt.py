#!/usr/bin/python3.3
import re
import sys

global legnth,BPMisChanged,SCRisChanged,firstLine,DEL
global BPM,SCR,MEA,BARLINEON,newline,lastLegnth,BalPos

def getInfo():
    tjaInfoDic = {}
    tjaInfoList = tjaFile.split("\n")
    for line in tjaInfoList:
        list=line.split(":")
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
            tjaFile = tjaFile.read()
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

def fumenComment(line):
    if (line == "#GOGOSTART"):
        newline.append("gg")
    elif (line == "#GOGOEND"):
        newline.append("g")
    elif (line.startswith("#BPMCHANGE")):
        BPM = float(re.sub("^[^\d.-]+", "", line))
        BPMisChanged = True
        SCRisChanged = True
    elif (line.startswith("#SCROLL")):
        SCR = float(re.sub("^[^\d.-]+", "", line))
        SCRisChanged = True
    elif (line.startswith("#MEASURE")):
        MEA = float(eval(re.sub("^[^\d/]+", "", line)))
    elif (line.startswith("#DELAY")):
        DEL = float(re.sub("^[^\d.-]+", "", line))
        DEL_str = "u("+str(DEL)+"),"
        newline.append(DEL_str)
        BPMisChanged = True
    elif (line == "#BARLINEON"):
        BARLINEON = True
    elif (line == "#BARLINEOFF"):
        BARLINEON = False
    elif (line.startswith("#END")):
        print("轉換完成! 按任意鍵退出. \nFile converted! Press any key to exit.")
        input()
        sys.exit()
        
def noteConvert(line):
    line = re.sub(r"0", ",", line)
    line = re.sub(r"1", "1,", line)
    line = re.sub(r"2", "2,", line)
    line = re.sub(r"3", "3,", line)
    line = re.sub(r"4", "4,", line)
    line = re.sub(r"5", "55,", line)
    line = re.sub(r"6", "66,", line)
    return line
    
tjaFile = fileOpen()
output = open(sys.argv[1]+".data.txt", 'w+')
tjaParted = tjaFile.partition("#START")
tjaInfoDic = getInfo()
infoWrite()
tjaFumen = re.split(',', re.sub("\n+", "\n", tjaParted[2]))
BPM,SCR,MEA,BARLINEON,newline,lastLegnth,BalPos = float(tjaInfoDic["BPM"]),1,1,True,[],0,0
for line in tjaFumen:
    legnth,BPMisChanged,SCRisChanged,firstLine,DEL = 0,False,False,True,0
    line = re.split('\n', line)
    del line[0]
    for line in line:
        if (line.startswith("#")):
            fumenComment(line)
        elif (line):
            legnth = (len(line)) + legnth
            line = noteConvert(line)
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
            line = re.sub(r"8", "567,", line)
            newline.append(line)
        else:
            newline.append(",,,,,,,,,,,,,,,,")
    if ((legnth != MEA*16) and (legnth != 0)) or (BPMisChanged == True) or (legnth != lastLegnth and (lastLegnth and legnth) != 0):
            unit_time = (60/BPM)/(legnth/4)
            unit_str = "u("+str(unit_time)+")"
            if (DEL == 0):
                newline.insert(0,unit_str)
            else:
                newline.insert(len(newline)-1, unit_str)
            BPMisChanged = False
            lastLegnth = legnth
    if (SCRisChanged == True):
            SCR_time = (60/BPM)/SCR
            SCR_str = "s("+str(SCR_time)+")"
            newline.insert(0,SCR_str)
            SCRisChanged == False
    for line in newline:
        if ((BARLINEON == True) and (firstLine == True)):
            if (line[0] == ","):
                output.write('\n' + line[:0] + '|' + line[0:])
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
