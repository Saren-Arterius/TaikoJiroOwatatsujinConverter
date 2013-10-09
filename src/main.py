#!/usr/bin/python3.3
import re
import sys

global songInfo, fumenInfo, listf

def fileOpen(arg):
    if (len(sys.argv) <= 1):
        print('未指定TJA檔案\nTJA file not specified.')
        input()
        raise Exception('TJA file not specified.') 
    with open(sys.argv[arg], "rt") as tjaFile:
        tjaFile = re.sub("\r", "", tjaFile.read())
    if ((tjaFile.find("#START")) == -1):
        TJAError[sys.argv[arg]] = 'TJA格式錯誤, TJA檔案內不含"#START"\nTJA file does not include "#START"'
        print('TJA格式錯誤')
    elif ((tjaFile.find("#END")) == -1):
        TJAError[sys.argv[arg]] = 'TJA格式錯誤, TJA檔案內不含"#END"\nTJA file does not include "#END"'
    tjaFile = re.split('\n', re.sub("\n+", "\n", tjaFile))
    return tjaFile
    
def parseInit():
    parsingFumenNow = False
    songInfo["LEVEL"], songInfo["BALLOON"], songInfo["SCOREINIT"], songInfo["SCOREDIFF"] = {}, {}, {}, {}
    for line in tjaFile:
        if line:
            if (line.startswith("#START")):
                parsingFumenNow = True
            elif (line.startswith("#END") ):
                parsingFumenNow = False
            elif (parsingFumenNow == True):
                fumenParse(line)
            elif ( not (line.startswith("/") or re.match("\d", line[0]) or parsingFumenNow == True or line.startswith("#")) ):
                getInfo(line)

def getInfo(line):
    global listf
    listf = line.split(":",1)
    key, val = listf
    try:
        if (key.startswith("COURSE")):
            if (val.lower() == "easy"):
                fumenInfo[key] = 0
            elif (val.lower() == "normal"):
                fumenInfo[key] = 1
            elif (val.lower() == "hard"):
                fumenInfo[key] = 2
            elif (val.lower() == "oni"):
                fumenInfo[key] = 3
            else:
                fumenInfo[key] = val
            fumen[fumenInfo["COURSE"]] = []
        elif (key.startswith("LEVEL")):
            songInfo[key][fumenInfo["COURSE"]] = val
        elif (key.startswith("BALLOON")):
            val = val.split(",")
            songInfo[key][fumenInfo["COURSE"]] = val
        elif (key.startswith("SCOREINIT")):
            songInfo[key][fumenInfo["COURSE"]] = val
        elif (key.startswith("SCOREDIFF")):
            songInfo[key][fumenInfo["COURSE"]] = val
        else:
            songInfo[key] = val
    except KeyError:
        pass
        
def fumenParse(line):
    global tempFumen
    if not (line.startswith("#")):
        line = re.sub(r"(?<=\d)", "`", line)
    line = re.split("`", line)
    if not line[-1]:
        del line[-1]
        tempFumen.append(line)
    elif (line[-1] == ","):
        del line[-1]
        tempFumen.append(line)
        tempFumen = [item for sublist in tempFumen for item in sublist]
        fumen[fumenInfo["COURSE"]].append(tempFumen)
        tempFumen = []
    else:
        tempFumen.append(line)

def convertInit():
    global fumenInfo
    print("開始轉換/Started converting \"",songInfo["TITLE"],"\"\n",sep="")
    for key, val in fumen.items():
        OWTFumen[key] = []
        fumenInfo["diff"],fumenInfo["initTimes"],fumenInfo["diffTimes"],fumenInfo["CurCombo"],fumenInfo["GOGOTIME"],fumenInfo["legnth"],fumenInfo["CurCOURSE"],fumenInfo["BPM"],fumenInfo["SCRfac"],fumenInfo["MEA"],fumenInfo["BARLINEON"],fumenInfo["lastLegnth"],fumenInfo["BalPos"],fumenInfo["lastUnitT"],fumenInfo["lastScrT"],fumenInfo["BPMisChanged"],fumenInfo["SCRisChanged"] = 0,0,0,0,False,0,key,float(songInfo["BPM"]),float(1),float(1),True,0,0,0,0,False,False
        for seq in val:
            fumenInfo["firstLine"] = True
            for note in seq:
                if str(note).isdigit():
                    fumenInfo["legnth"] = fumenInfo["legnth"] + 1
            for note in seq:
                if note.startswith("#"):
                    note = fumenComment(note)
                else:
                    note = noteConvert(note)
                    fumenInfo["firstLine"] = False
                    OWTFumen[key].append(unitTimeChange())
                    OWTFumen[key].append(scrollTimeChange())
                OWTFumen[key].append(note)
            OWTFumen[key].append("\n")
            fumenInfo["lastLegnth"] = fumenInfo["legnth"]
            fumenInfo["legnth"] = 0
        scoreCalc()
        
def fumenComment(note):
    global fumenInfo
    if (note == "#GOGOSTART"):
        note = "gg\n"
        fumenInfo["GOGOTIME"] = True
    elif (note == "#GOGOEND"):
        note = "g\n"
        fumenInfo["GOGOTIME"] = False
    elif (note.startswith("#BPMCHANGE")):
        fumenInfo["BPM"] = float(re.sub("^[^\d.-]+", "", note))
        unit_time = (60/fumenInfo["BPM"])/(fumenInfo["legnth"]/4)*fumenInfo["MEA"]
        unit_str = "u("+str(unit_time)+")\n"
        if (unit_time != fumenInfo["lastUnitT"]):
            note = unit_str
            fumenInfo["lastUnitT"] = unit_time
        else:
            note = None
        fumenInfo["SCRisChanged"] = True
    elif (note.startswith("#SCROLL")):
        fumenInfo["SCRfac"] = float(re.sub("^[^\d.-]+", "", note))
        fumenInfo["SCRisChanged"] = True
        note = None
    elif (note.startswith("#MEASURE")):
        fumenInfo["MEA"] = float(eval(re.sub("^[^\d/]+", "", note)))
        note = None
    elif (note.startswith("#DELAY")):
        DEL = float(re.sub("^[^\d.-]+", "", note))
        DEL_str = "u("+str(DEL)+"),\n"
        note = DEL_str
        fumenInfo["lastUnitT"] = DEL
        fumenInfo["BPMisChanged"] = True
    elif (note == "#BARLINEON"):
        fumenInfo["BARLINEON"] = True
        note = None
    elif (note == "#BARLINEOFF"):
        fumenInfo["BARLINEON"] = False
        note = None
    return note
        
def noteConvert(note):
    note = re.sub(r"0", "", note)
    if (note == "1" or note == "2"):
        fumenInfo["CurCombo"] = fumenInfo["CurCombo"] + 1
        if (fumenInfo["CurCombo"] in range(10,101,10) and (fumenInfo["CurCombo"] <= 100)):
            fumenInfo["diff"] = 1*(fumenInfo["CurCombo"]/10)
        if fumenInfo["GOGOTIME"]:
            fumenInfo["initTimes"] = fumenInfo["initTimes"] + 1.2
            fumenInfo["diffTimes"] = fumenInfo["diffTimes"] + fumenInfo["diff"]*1.2
        else:
            fumenInfo["initTimes"] = fumenInfo["initTimes"] + 1
            fumenInfo["diffTimes"] = fumenInfo["diffTimes"] + fumenInfo["diff"]
    if (note == "3" or note == "4"):
        fumenInfo["CurCombo"] = fumenInfo["CurCombo"] + 1
        if (fumenInfo["CurCombo"] in range(1,101,10) and (fumenInfo["CurCombo"] <= 100)):
            fumenInfo["diff"] = 1*(fumenInfo["CurCombo"]/10)
        if fumenInfo["GOGOTIME"]:
            fumenInfo["initTimes"] = fumenInfo["initTimes"] + 2.4
            fumenInfo["diffTimes"] = fumenInfo["diffTimes"] + fumenInfo["diff"]*2.4
        else:
            fumenInfo["initTimes"] = fumenInfo["initTimes"] + 2
            fumenInfo["diffTimes"] = fumenInfo["diffTimes"] + fumenInfo["diff"]*2
    if (note == "5"):
        note = "55"
        fumenInfo["WhatShouldBeEnded"] = "5"
    if (note == "6"):
        note = "66"
        fumenInfo["WhatShouldBeEnded"] = "6"
    if (note == "7"):
        try:
            note = "77("+songInfo["BALLOON"][fumenInfo["CurCOURSE"]][fumenInfo["BalPos"]]+")"
            fumenInfo["BalPos"] = fumenInfo["BalPos"] + 1
            fumenInfo["WhatShouldBeEnded"] = "7"
        except IndexError:
            pass
        except KeyError:
            print("有氣球音符但連打數未指定\nBalloon note detected, but hit count not specified\n")
    if (note == "8"):
        try:
            note = fumenInfo["WhatShouldBeEnded"]+""
        except KeyError:
            pass
    if (fumenInfo["firstLine"] and fumenInfo["BARLINEON"]):
        note = note+"|,"
    else:
        note = note+","
    return note

def unitTimeChange():
    global fumenInfo
    if ((fumenInfo["legnth"] != fumenInfo["MEA"]*16) and (fumenInfo["legnth"] != 0)) or (fumenInfo["BPMisChanged"] == True) or (fumenInfo["legnth"] != fumenInfo["lastLegnth"] and (fumenInfo["lastLegnth"] != 0) and (fumenInfo["legnth"] != 0)):
        unit_time = (60/fumenInfo["BPM"])/(fumenInfo["legnth"]/4)*fumenInfo["MEA"]
        fumenInfo["BPMisChanged"] = False
        if (unit_time != fumenInfo["lastUnitT"]):
            unit_str = "u("+str(unit_time)+")\n"
            fumenInfo["lastUnitT"] = unit_time
            return unit_str
        
def scrollTimeChange():
    global fumenInfo
    if (fumenInfo["SCRisChanged"] == True):
        SCR_time = (60/fumenInfo["BPM"])/fumenInfo["SCRfac"]
        fumenInfo["SCRisChanged"] == False
        if (fumenInfo["lastScrT"] != SCR_time):
            SCR_str = "\ns("+str(SCR_time)+")\n"
            fumenInfo["lastScrT"] = SCR_time
            return SCR_str

def scoreCalc():
    global fumenInfo
    try:
        songInfo["SCOREINIT"][fumenInfo["CurCOURSE"]], songInfo["SCOREDIFF"][fumenInfo["CurCOURSE"]]
    except KeyError:
        try:
            songInfo["LEVEL"][fumenInfo["CurCOURSE"]]
            print("程式偵測不到譜面的初項和等差，正在盡量計算中...\nSCOREINIT or SCOREDIFF not detected, calculating...\n")
            balloonTotalHits,balloons,scores = 0,0,{}
            if str(fumenInfo["CurCOURSE"]) == "0":
                maxScore = 280000 + int(songInfo["LEVEL"][fumenInfo["CurCOURSE"]])*20000
            elif str(fumenInfo["CurCOURSE"]) == "1":
                maxScore = 350000 + int(songInfo["LEVEL"][fumenInfo["CurCOURSE"]])*50000
            elif str(fumenInfo["CurCOURSE"]) == "2":
                maxScore = 500000 + int(songInfo["LEVEL"][fumenInfo["CurCOURSE"]])*50000
            elif str(fumenInfo["CurCOURSE"]) == "3":
                maxScore = 650000 + int(songInfo["LEVEL"][fumenInfo["CurCOURSE"]])*50000
                if str(songInfo["LEVEL"][fumenInfo["CurCOURSE"]]) == "10":
                    maxScore = maxScore+50000
            try:
                for hits in songInfo["BALLOON"][fumenInfo["CurCOURSE"]]:
                    balloonTotalHits = balloonTotalHits+int(hits)
                    balloons = balloons + 1
            except KeyError:
                pass
            except ValueError:
                pass
            try:
                levelMaxScore = maxScore
                try:
                    maxScore = maxScore-(balloonTotalHits*300)-(balloons*5000)
                except KeyError:
                    pass
                for scale in range(300,501,1):
                    scale = scale*0.01
                    y = maxScore/((fumenInfo["initTimes"]*scale)+fumenInfo["diffTimes"])
                    x = y*scale
                    scores[(round(fumenInfo["initTimes"]*(round(x/10)*10)+fumenInfo["diffTimes"]*(round(y/10)*10)))] = [round(x/10)*10,round(y/10)*10]
                songInfo["SCOREINIT"][fumenInfo["CurCOURSE"]] = str(scores[min(scores, key=lambda x:abs(x-maxScore))][0])
                songInfo["SCOREDIFF"][fumenInfo["CurCOURSE"]] = str(scores[min(scores, key=lambda x:abs(x-maxScore))][1])
                print("難度/COURSE=",fumenInfo["CurCOURSE"],", 等級/LEVEL=",songInfo["LEVEL"][fumenInfo["CurCOURSE"]],", 連擊/Combos=",fumenInfo["CurCombo"],sep="")
                print("等級天井/Level Max Score=",levelMaxScore,", 曲目天井/Song Max Score=",maxScore,sep="")
                print("初項/SCOREINIT=",songInfo["SCOREINIT"][fumenInfo["CurCOURSE"]],", 等差/SCOREDIFF=",songInfo["SCOREDIFF"][fumenInfo["CurCOURSE"]], ", 比率/Ratio=",round(int(songInfo["SCOREINIT"][fumenInfo["CurCOURSE"]])/int(songInfo["SCOREDIFF"][fumenInfo["CurCOURSE"]]),2),":1",sep="")
                print("預計天井(未計算連打)/Max Score without Renda=",round(fumenInfo["initTimes"]*(round(x/10)*10)+fumenInfo["diffTimes"]*(round(y/10)*10)),"\n",sep="")
            except UnboundLocalError:
                print('未支援的難度 "',fumenInfo["CurCOURSE"],'"，略過分數計算...\nUnsupported COURSE "',fumenInfo["CurCOURSE"],'", skipping calculation...\n')
        except KeyError:
            print('未指定難度',[fumenInfo["CurCOURSE"]],'的等級，略過分數計算...\nLEVEL of a COURSE not specified, skipping calculation...\n')
            
def infoWrite():
    output.write("head=owata1\n&format=1")
    output.write("\n&title="+songInfo["TITLE"])
    if ("SONGVOL" in songInfo):
        output.write("\n&bgm_vol="+songInfo["SONGVOL"])
    if ("SEVOL" in songInfo):
        output.write("\n&se_vol="+songInfo["SEVOL"])
    if ("COURSE" and "LEVEL" in songInfo):
        for course,level in songInfo["LEVEL"].items():
            output.write("\n&level"+str((int(course)+1))+"="+level)
    else:
        print('TJA格式錯誤, TJA檔案內不含COURSE或LEVEL\nTJA File does not include "COURSE" nor "LEVEL"')
        input()
        raise Exception('TJA File does not include "COURSE" nor "LEVEL"')
    if ("OFFSET" in songInfo):
        output.write("\n&start_time="+str(float(songInfo["OFFSET"])*-1))
    if ("BPM" in songInfo):
        output.write("\n&unit_time="+str(60/float(songInfo["BPM"])/4))
        output.write("\n&scroll_time="+str(60/float(songInfo["BPM"])))
    if ("SCOREINIT" and "SCOREDIFF" in songInfo):
        for course in songInfo["LEVEL"]:
            try:
                output.write("\n&score"+str(int(course)+1)+"="+songInfo["SCOREINIT"][course]+","+songInfo["SCOREDIFF"][course])
            except KeyError:
                print('略過分數初項公差寫入...\nSkipping writting of "SCOREINIT" and "SCOREDIFF"...\n')
    output.write("\n&bunki=0,0,0,0")

def fumenWrite():
    for course,fumen in OWTFumen.items():
        output.write("\n&seq"+str(int(course)+1)+"=\n")
        for note in fumen:
            if note:
                output.write(note)

TJAConverted, TJAError = [], {}
for arg in range(1,len(sys.argv)):
    fumenInfo, songInfo, fumen, OWTFumen, tempFumen = {}, {}, {}, {}, []
    try:
        tjaFile = fileOpen(arg)
        try:
            parseInit()
        except KeyError:
            TJAError[sys.argv[arg]] = 'TJA格式錯誤, 請設定"COURSE"，並把"COURSE"放在"LEVEL"、"BALLOON"、"SCOREINIT"、"SCOREDIFF"的上面\nPlease specify "COURSE", and place "COURSE" above "LEVEL", "BALLOON", "SCOREINIT", "SCOREDIFF"'
        except ValueError:
            TJAError[sys.argv[arg]] = 'TJA格式錯誤, 未支援的註譯:'+listf[0]+'\nUnsupported comment:'+listf[0]
        else:
            convertInit()
            output = open(sys.argv[arg]+".data.txt", 'w+')
            infoWrite()
            fumenWrite()
            print("完成轉換/Finished converting \"",songInfo["TITLE"],"\"",sep="")
            TJAConverted.append(songInfo["TITLE"])
    except UnicodeDecodeError:
        TJAError[sys.argv[arg]] = 'TJA含有亂碼，請移除TITLE和SUBTITLE的內容\nYour TJA file contains character that cannot be decoded. Please remove any content of TITLE and SUBTITLE.'
    except ZeroDivisionError:
        TJAError[sys.argv[arg]] = '未支援的譜面寫作格式\nUnsupported TJA format'

if TJAConverted:
    print("\n以下曲目轉換完成。\nFinished converting the following songs.\n")
    successlog = open(sys.argv[0]+".success.log", 'w+')
    for song in TJAConverted:
        print(song)
        successlog.write(song+"\n")
if TJAError:
    print("\n以下曲目檔案轉換失敗。\nFailed converting the following songs.\n")
    errorlog = open(sys.argv[0]+".error.log", 'w+')
    for file,error in TJAError.items():
        print(file,"\n",error,"\n",sep="")
        errorlog.write(file+"\n"+error+"\n\n")
print("請按任意鍵退出。\nPress any key to exit.")
input()
sys.exit()