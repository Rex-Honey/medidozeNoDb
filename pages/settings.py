# pages/settings_page.py
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import QTimer,QThread,pyqtSignal
import os, pyodbc,win32print,json,requests
from functools import partial
from datetime import datetime, timedelta
from otherFiles.common import dictfetchall
from decimal import Decimal, ROUND_DOWN


class Worker(QThread):
    updateDispenseData = pyqtSignal(str,str,str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.count=0

    def updateRefillForCycleData(self,data):
        try:
            localConn=data['localConn']
            local_cursor = localConn.cursor()
            loginUser=data['loginUser']
            checkReasonList=data['checkReasonList']
            reDataDict=data['reDataDict']
            stopDate=data['stopDate']
            reefdate=data['startDate']

            rxID=data['rxData']['rxID']
            patiendID=data['rxData']['patientID']
            scheduleType=data['rxData']['scheduleType']
            totRemaining=data['rxData']['rxQty']
            carryEnabled=data['rxData']['carryEnabled']

            # if rxID == 491362:
            #     print()

            prevDate=None
            emergencyCount=0

            totDays=0
            cycleData=data['cycleData']
            customCycleData = {}
            for row in cycleData:
                row['dose']=str(int(row['dose'])) if row['dose'].is_integer() else str(row['dose'])
                if row['cycle'] not in customCycleData:
                    customCycleData[row['cycle']]={}
                    customCycleData[row['cycle']]['frequency']=row['frequency']
                    customCycleData[row['cycle']]['days']=row['days']
                    customCycleData[row['cycle']]['doseArr']=[row['dose']]
                    totDays+=row['days']
                else:
                    customCycleData[row['cycle']]['doseArr'].append(row['dose'])

            local_cursor.execute(f"DELETE FROM refill WHERE rxId = {rxID}")
            if scheduleType == "Daily":
                print("======== DAILY SCHEDULE ========")
                for cycle,cycleData in customCycleData.items():
                    if stopDate:
                        if reefdate>stopDate:
                            print("refill stopped due to stop date")
                            break
                    dayVal=cycleData['days']
                    doseArr=cycleData['doseArr']
                    frequency=cycleData['frequency']

                    witnessVal=float(doseArr[0])
                    if witnessVal.is_integer():
                        witness = int(witnessVal)
                    else:
                        witness = witnessVal
                    
                    dayCarry=0
                    if len(doseArr) == 1:
                        dayCarryStr="0"
                    else:
                        dayCarryStr=",".join(doseArr[1:])
                        for i in range(1,len(doseArr)):
                            valueFloat=float(doseArr[i])
                            if valueFloat.is_integer():
                                carryValue = int(valueFloat)
                            else:
                                carryValue = valueFloat
                            dayCarry+=carryValue
                
                    loop=0
                    carryStr=str(dayCarryStr)
                    while loop<dayVal:
                        if stopDate:
                            if reefdate>stopDate:
                                print("refill stopped due to stop date")
                                break
                        totProcessing=witness+dayCarry
                        totRemaining -= totProcessing
                        reReason=reDataDict.get(rxID,{}).get(reefdate.date(),None)
                        if reReason not in checkReasonList:
                            reReason=None
                        print("-- UPDATING REFILL FOR DATE: ",reefdate.date())
                        if prevDate:
                            query = """INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, frequency, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                            params = (rxID, patiendID, reefdate, prevDate, witness, carryStr, frequency, emergencyCount, totProcessing, totRemaining, reReason, loginUser, loginUser, datetime.now(), datetime.now())
                        else:
                            query = """INSERT INTO refill (rxID, patientID, reefDate, witness, carry, frequency, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                            params = (rxID, patiendID, reefdate, witness, carryStr, frequency, emergencyCount, totProcessing, totRemaining, reReason, loginUser, loginUser, datetime.now(), datetime.now())
                        local_cursor.execute(query, params)
                        if reReason:
                            totRemaining=totRemaining+totProcessing                     
                        else:
                            prevDate = reefdate
                            loop+=1
                        reefdate += timedelta(days=1)

            elif scheduleType in ("Changing","Weekly","Custom"):
                print(f"======== {scheduleType} Schedule ========")
                weekDay=reefdate.weekday()
                res_arr=[]
                res_str=""
                string=data['rxData']['scDays']
                for i in range(weekDay+1, totDays+weekDay+1):
                    char = string[i % len(string)]
                    res_str+=str(char)
                prev_ind=""
                count=1
                firstDay=False
                last_ind=totDays-1
                for ind, i in enumerate(res_str):
                    if i==" " and ind==0:
                        firstDay=True
                        res_arr.append(1)
                        prev_ind=ind
                    elif i==" " and ind==last_ind:
                        if prev_ind=="":
                            prev_ind=ind-1
                        count+=1
                        res_arr[prev_ind]=1*count
                        res_arr.append("")
                    elif i==" ":
                        if prev_ind=="":
                            prev_ind=ind-1
                        count+=1
                        res_arr.append("")
                    else:
                        if firstDay:
                            res_arr[prev_ind]=1*count
                            prev_ind=ind
                            firstDay=False
                        else:
                            if prev_ind!="":
                                res_arr[prev_ind]=1*count
                                prev_ind=""
                        res_arr.append(1)
                        count=1
                print(res_arr)

                for cycle,cycleData in customCycleData.items():
                    if stopDate:
                        if reefdate>stopDate:
                            print("refill stopped due to stop date")
                            break
                    dayVal=cycleData['days']
                    doseArr=cycleData['doseArr']
                    frequency=cycleData['frequency']

                    witnessVal=float(doseArr[0])
                    if witnessVal.is_integer():
                        witness = int(witnessVal)
                    else:
                        witness = witnessVal

                    dayCarry=0
                    if len(doseArr) == 1:
                        dayCarryStr="0"
                    else:
                        dayCarryStr=",".join(doseArr[1:])
                        for i in range(1,len(doseArr)):
                            valueFloat=float(doseArr[i])
                            if valueFloat.is_integer():
                                carryValue = int(valueFloat)
                            else:
                                carryValue = valueFloat
                            dayCarry+=carryValue
                    loop=0
                    while loop<dayVal:
                        if stopDate:
                            if reefdate>stopDate:
                                print("refill stopped due to stop date")
                                break
                        item=res_arr[0]
                        if item:
                            carry=0
                            carryStr=str(carry)
                            if carryEnabled=="N":
                                item=1
                            if item==1 and dayCarry>0:
                                carry=dayCarry
                                carryStr=str(dayCarryStr)
                            elif item>1:
                                if dayCarry==0:
                                    carry=witness*(item-1)
                                    carryStr=(','+str(witness))*(item-1)
                                    carryStr=carryStr[1:]
                                else:
                                    carry=((witness+dayCarry)*(item))-witness
                                    carryStr=str(dayCarryStr)+(','+str(witness)+','+str(dayCarryStr))*(item-1)
                            totProcessing=witness+carry
                            totRemaining=totRemaining-totProcessing
                            reReason=reDataDict.get(rxID,{}).get(reefdate.date(),None)
                            if reReason not in checkReasonList:
                                reReason=None
                            print("-- UPDATING REFILL FOR DATE: ",reefdate.date())
                            if prevDate:
                                query="""
                                    INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry,frequency, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """
                                params=(rxID,patiendID,reefdate,prevDate,witness,carryStr,frequency,emergencyCount,totProcessing,totRemaining,reReason,loginUser,loginUser,datetime.now(),datetime.now())
                            else:
                                query="""
                                    INSERT INTO refill (rxID, patientID, reefDate, witness, carry,frequency, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """
                                params=(rxID,patiendID,reefdate,witness,carryStr,frequency,emergencyCount,totProcessing,totRemaining,reReason,loginUser,loginUser,datetime.now(),datetime.now())
                            local_cursor.execute(query,params)
                            if reReason:
                                totRemaining=totRemaining+totProcessing
                            else:
                                prevDate=reefdate
                                loop+=1
                                res_arr.pop(0)
                        reefdate+=timedelta(days=1)

            elif scheduleType=='EOD':
                print("======== EOD SCHEDULE ========")

                local_cursor.execute(f"Delete FROM refill WHERE rxId = {rxID}")

                for cycle,cycleData in customCycleData.items():
                    if stopDate:
                        if reefdate>stopDate:
                            print("refill stopped due to stop date")
                            break
                    dayVal=cycleData['days']
                    doseArr=cycleData['doseArr']
                    frequency=cycleData['frequency']

                    witnessVal=float(doseArr[0])
                    if witnessVal.is_integer():
                        witness = int(witnessVal)
                    else:
                        witness = witnessVal

                    dayCarry=0
                    if len(doseArr) == 1:
                        dayCarryStr="0"
                    else:
                        dayCarryStr=",".join(doseArr[1:])
                        for i in range(1,len(doseArr)):
                            valueFloat=float(doseArr[i])
                            if valueFloat.is_integer():
                                carryValue = int(valueFloat)
                            else:
                                carryValue = valueFloat
                            dayCarry+=carryValue

                    carryStr="0"
                    carry=0
                    if carryEnabled=="Y":
                        if dayCarry>0:
                            carryV=witness+(dayCarry)*2
                            carryStrV=dayCarryStr+","+str(witness)+','+dayCarryStr
                        else:
                            carryV=witness
                            carryStrV=str(witness)
                    loop=0
                    while loop<dayVal:
                        if stopDate:
                            if reefdate>stopDate:
                                print("refill stopped due to stop date")
                                break
                        if loop % 2 == 0:
                            carry=carryV
                            carryStr=carryStrV
                        else:
                            carry=0
                            carryStr="0"
                        totProcessing=witness+carry
                        totRemaining=totRemaining-totProcessing
                        reReason=reDataDict.get(rxID,{}).get(reefdate.date(),None)
                        if reReason not in checkReasonList:
                            reReason=None
                        print("-- UPDATING REFILL FOR DATE: ",reefdate.date())
                        if prevDate:
                            query="INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry,frequency, emergencyCount, totProcessing, totRemaining, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                            params=(rxID,patiendID,reefdate,prevDate,witness,carryStr,frequency,emergencyCount,totProcessing,totRemaining,loginUser,loginUser,datetime.now(),datetime.now())
                        else:
                            query="INSERT INTO refill (rxID, patientID, reefDate, witness, carry,frequency, emergencyCount, totProcessing, totRemaining, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                            params=(rxID,patiendID,reefdate,witness,carryStr,frequency,emergencyCount,totProcessing,totRemaining,loginUser,loginUser,datetime.now(),datetime.now())
                        local_cursor.execute(query, params)
                        if reReason:
                            totRemaining=totRemaining+totProcessing
                        else:
                            prevDate=reefdate
                            loop+=1
                        reefdate+=timedelta(days=2)

            for _ in range(15):
                emergencyCount+=1
                carryStr="0"
                totRemaining=0
                totProcessing=witness
                query="INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, emergencyCount, totProcessing, totRemaining, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                params=(rxID,patiendID,reefdate,prevDate,witness,carryStr,emergencyCount,totProcessing,totRemaining,loginUser,loginUser,datetime.now(),datetime.now())
                local_cursor.execute(query, params)
                prevDate=reefdate
                reefdate+=timedelta(days=1)
            print("======== RX UPDATED ========")
            # self.fetchDispenseData()
            print()
            return {"status":"success"}
        except Exception as e:
            print("Error:",e)
            return {"status":"error","message":str(e)}

    def updateRefillData(self, data):
        try:
            localConn=data['localConn']
            loginUser=data['loginUser']
            row=data['row']
            startDate=data['startDate']
            stopDate=data['stopDate']
            reDataDict=data['reDataDict']
            checkReasonList=data['checkReasonList']
            witness=data['witness']
            totRemaining=data['totRemaining']
            totDays=data['totDays']
            local_cursor = localConn.cursor()
            
            emergencyCount=0
            prevDate=None
            print("======== DELETING OLD REFILL DATA ========")
            query=f"delete from refill where rxID={row['RXNUM']}"
            local_cursor.execute(query)

            # print("-- SCDAYS:",row['SCDAYS'])
            if not row['SCDAYS'] or len(str(row['SCDAYS']).strip()) in (0,7):
                reefdate=startDate
                for i in range(totDays):
                    if stopDate:
                        if reefdate>stopDate:
                            print("refill stopped due to stop date")
                            break
                    carry=0
                    carryStr="0"
                    totProcessing=witness+carry
                    totRemaining=totRemaining-totProcessing
                    reReason=reDataDict.get(row['RXNUM'],{}).get(reefdate.date(),None)
                    if reReason not in checkReasonList:
                        reReason=None
                    print("-- UPDATING REFILL FOR DATE: ",reefdate.date())
                    if prevDate:
                        query="""
                            INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        paramValues=(row['RXNUM'], row['RXPANUM'], reefdate, prevDate, witness, carryStr,emergencyCount, totProcessing, totRemaining, reReason, loginUser, loginUser, datetime.now(), datetime.now())
                    else:
                        query="""
                            INSERT INTO refill (rxID, patientID, reefDate, witness, carry, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        paramValues=(row['RXNUM'], row['RXPANUM'], reefdate, witness, carryStr,emergencyCount, totProcessing, totRemaining, reReason, loginUser, loginUser, datetime.now(), datetime.now())
                    local_cursor.execute(query,paramValues)
                    if reReason:
                        totRemaining=totRemaining+totProcessing
                    else:
                        prevDate=reefdate
                    reefdate+=timedelta(days=1)
            else:
                print('-- Found Schedule')
                weekDay=startDate.weekday()+1
                string = row['SCDAYS']
                res_str=""
                # --------------- res_str ------------------
                for i in range(weekDay, totDays+weekDay):
                    char = string[i % len(string)]
                    res_str+=str(char)

                # --------------- res_arr ------------------
                res_arr=[]
                prev_ind=""
                count=1
                firstDay=False
                last_ind=totDays-1
                for ind, i in enumerate(res_str):
                    if i==" " and ind==0:
                        firstDay=True
                        res_arr.append(1)
                        prev_ind=ind
                    elif i==" " and ind==last_ind:
                        if prev_ind=="":
                            prev_ind=ind-1
                        count+=1
                        res_arr[prev_ind]=1*count
                        res_arr.append("")
                    elif i==" ":
                        if prev_ind=="":
                            prev_ind=ind-1
                        count+=1
                        res_arr.append("")
                    else:
                        if firstDay:
                            res_arr[prev_ind]=1*count
                            prev_ind=ind
                            firstDay=False
                        else:
                            if prev_ind!="":
                                res_arr[prev_ind]=1*count
                                prev_ind=""
                        res_arr.append(1)
                        count=1
                # print(res_arr)
                #  ------------------ calculate carry and save refill --------------------------
                reefdate=startDate
                # for i in res_arr:
                while totRemaining>0:
                    if stopDate:
                        if reefdate>=stopDate:
                            break
                    item=res_arr[0]
                    if item:
                        if item>1:
                            carry=witness*(item-1)
                            carryStr=(','+str(witness))*(item-1)
                            carryStr=carryStr[1:]
                        else:
                            carry=0
                            carryStr="0"
                        totProcessing=witness+carry
                        totRemaining=totRemaining-totProcessing
                        reReason=reDataDict.get(row['RXNUM'],{}).get(reefdate.date(),None)
                        if reReason not in checkReasonList:
                            reReason=None
                        if prevDate:
                            query="""
                                INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """
                            paramValues=(row['RXNUM'], row['RXPANUM'], reefdate, prevDate, witness, carryStr,emergencyCount, totProcessing, totRemaining, reReason, loginUser, loginUser, datetime.now(), datetime.now())
                        else:
                            query="""
                                INSERT INTO refill (rxID, patientID, reefDate, witness, carry, emergencyCount, totProcessing, totRemaining, reReason, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """
                            paramValues=(row['RXNUM'], row['RXPANUM'], reefdate, witness, carryStr,emergencyCount, totProcessing, totRemaining, reReason, loginUser, loginUser, datetime.now(), datetime.now())
                        print("-- UPDATING REFILL FOR DATE: ",reefdate.date())
                        local_cursor.execute(query,paramValues)
                        if reReason:
                            totRemaining=totRemaining+totProcessing
                        else:
                            prevDate=reefdate
                    reefdate+=timedelta(days=1)
                    res_arr.pop(0)

            totRemaining=0
            carryStr="0"
            for _ in range(15):
                emergencyCount+=1
                query="""
                IF NOT EXISTS (SELECT 1 FROM refill WHERE rxID = ? AND CONVERT(date,reefDate) = ?)
                BEGIN
                    INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, emergencyCount, totProcessing, totRemaining, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                END
                """
                paramValues=(row['RXNUM'],reefdate, row['RXNUM'], row['RXPANUM'], reefdate, prevDate, witness, carryStr,emergencyCount, totProcessing, totRemaining, loginUser, loginUser, datetime.now(), datetime.now())
                local_cursor.execute(query,paramValues)
                prevDate=reefdate
                reefdate+=timedelta(days=1)
            return {"status":"success"}
        except Exception as e:
            print(e)
            return {"status":"error","message":str(e)}

    def update_dispense_data(self,localConn,liveConn,loginUser,triggerBy,getDateApiUrl,pharmacyId,apiToken):
        try:
            # req_din=['67000005','67000006','67000007','67000008','67000013','67000014','67000015','67000016','66999997','66999998','66999999','67000000','67000001','67000002','67000003','67000004','2394596']
            # metadol=['67000005','67000006','67000007','67000008','67000013','67000014','67000015','67000016']
            # methadose=['66999997','66999998','66999999','67000000','67000001','67000002','67000003','67000004','2394596']
            local_cursor = localConn.cursor()
            local_cursor.execute("SELECT * FROM din_groups")
            medicationArr = [med['medication'] for med in dictfetchall(local_cursor)]
            checkReasonList=['RE','RU','RR','RC']

            # medicationArr = []
            # medicationArr = ['metadol']
            # medicationArr = ['methadose']
            # medicationArr = ['metadol','methadose']
            if not medicationArr:
                self.updateDispenseData.emit("success","Medication not found",triggerBy)
                print("Please add dins first")
                return
            if len(medicationArr) == 1:
                formatMedication = "('{}')".format(medicationArr[0])
            else:
                formatMedication=tuple(medicationArr)

            print("======== GETTING REQUIRE DINS ========")
            query = f"SELECT din_number from din join din_groups on din.din_group_id=din_groups.id where medication IN {formatMedication}"
            local_cursor.execute(query)
            req_din = [value[0] for value in local_cursor.fetchall()]
            print(req_din)
            print()

            currentDateTime=datetime.now()
            currentDateTime = datetime(2025, 9, 7)
            formattedcurrentDateTime = currentDateTime.strftime('%Y-%m-%d %H:%M:%S')

            live_cursor = liveConn.cursor()
            print("======== FETCHING TODAY RX OF DINS ========")
            live_cursor.execute(f"select RERXNUM, REREASON from refill where REDIN IN {tuple(req_din)} AND CONVERT(date,REEFDATE)='{formattedcurrentDateTime}'")
            data=dictfetchall(live_cursor)
            if not data:
                self.updateDispenseData.emit("success","No Rx found in winrx database for today",triggerBy)
                print("-- No Rx found in winrx database for today --")
                return
            
            print("======== CREATING RX LIST ========")
            rxList = [int(row['RERXNUM']) for row in data]
            if len(rxList)==1:
                rxList="({})".format(rxList[0])
            else:
                rxList=tuple(rxList)
            print(rxList)
            print()

            print("======== CREATING DICTIONARY FOR RE REASONS DATES ========")
            reDataDict={}
            live_cursor.execute(f"select RERXNUM, REEFDATE, REREASON from refill where RERXNUM IN {rxList} and reReason is not null")
            reData=dictfetchall(live_cursor)
            for dt in reData:
                reReefDate=dt['REEFDATE'].date()
                reRxNum=int(dt['RERXNUM'])
                reReason=dt['REREASON']
                if reRxNum not in reDataDict:
                    reDataDict[reRxNum]={reReefDate:reReason}
                else:
                    reDataDict[reRxNum][reReefDate]=reReason

            aiDateData={}
            # if getDateApiUrl and pharmacyId and apiToken:
            #     print("======== GETTING AI DATES OF TODAY RX'S ========")
            #     params={
            #         "pharmacy_id":pharmacyId,
            #         "rxnumber":rxList
            #     }
            #     headers = {
            #         "X-API-KEY": apiToken,
            #         "Content-Type": "application/json"
            #     }
            #     response=requests.request("GET", getDateApiUrl, headers=headers, data=json.dumps(params))
            #     if response.status_code==200:
            #         responseData=response.json()
            #         aiDateData=responseData['data']
            #     else:
            #         print(f"Error: {response.json()}")
            
            print("======== GETTING RX AND PATIENT DATA OF TODAY RX'S ========")
            live_cursor.execute(f"select patient.PAROUTE, patient.PAGIVEN, patient.PASURNAME, patient.PASEX, patient.PAAREA, patient.PAPHONE, RXNUM, RX.RXPANUM, RX.RXTYPE, RX.RXSIG, RX.RXDR1ST, RX.RXDRLAST, RX.RXDIN, RX.RXORIG, RX.RXSTOP, RX.RXQTY, RX.RXDAYS, RX.RXLIM, RX.RXDRUG, RX.RXSTAT, RX.RXNOTE, SCHEDULE.SCDAYS from RX JOIN patient ON patient.PANUM = RX.RXPANUM LEFT JOIN SCHEDULE ON RX.RXNUM=SCHEDULE.SCRXNUM where RX.RXNUM IN {tuple(rxList)} ORDER BY RX.RXNUM")
            data=dictfetchall(live_cursor)

            local_cursor = localConn.cursor()
            zero_val=0
            skippedRx={}
            for row in data:
                print("\n========================= PROCESSING RX:",int(row['RXNUM'])," ==========================")
                if int(row['RXNUM']) == 684921:
                    print("")
                aiOrigDate=aiDateData.get(str(int(row['RXNUM'])),{}).get('ai_start_date',None)
                aiStopDate=aiDateData.get(str(int(row['RXNUM'])),{}).get('ai_stop_date',None)
                if row['RXORIG']:
                    startDate=row['RXORIG']
                elif aiDateData:
                    startDate=datetime.strptime(aiOrigDate, "%Y-%m-%d")
                else:
                    startDate=None
                if not startDate:
                    skippedRx[row['RXNUM']]="Don't get start date"
                    print("Skipped: Don't get start date")
                    continue

                print("======== UPDATING PATIENT DATA ========")
                phone=str(row['PAPHONE']).replace('-','')
                query="""
                IF EXISTS (SELECT 1 FROM patient WHERE id = ?)
                UPDATE patient SET route = ?, firstName = ?, lastName = ?, gender = ?, areaCode = ?, phone = ?, updatedBy = ?, updatedDate = ? WHERE id = ?
                ELSE
                INSERT INTO patient (id, route, firstName, lastName, gender, areaCode, phone, createdBy, updatedBy, createdDate, updatedDate) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """
                paramValues=(row['RXPANUM'], row['PAROUTE'], row['PAGIVEN'], row['PASURNAME'], row['PASEX'], row['PAAREA'], phone,loginUser, formattedcurrentDateTime, row['RXPANUM'], row['RXPANUM'],row['PAROUTE'], row['PAGIVEN'], row['PASURNAME'], row['PASEX'], row['PAAREA'], phone,loginUser,loginUser,formattedcurrentDateTime, formattedcurrentDateTime)
                local_cursor.execute(query, paramValues)
                
                rxStat=row['RXSTAT']
                # if row['RXSTOP']:
                if row['RXSTOP']:
                    stopDate=row['RXSTOP']
                elif aiDateData:
                    stopDate=datetime.strptime(aiStopDate, "%Y-%m-%d")
                else:
                    stopDate=None
                if stopDate and currentDateTime.date() >= stopDate.date():
                    rxStat='S'
                    if str(row['RXNOTE']).startswith('->'):
                        rxStat='Tsf'

                if len(str(row['SCDAYS']).strip()) in (0,7):
                    scheduleType='Daily'
                else:
                    scheduleType='New'

                if row['RXLIM']>0:
                    daily_qty=Decimal(row['RXQTY'])
                    totDays=int(row['RXLIM'])+1
                    totRemaining=Decimal(row['RXQTY']*totDays).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                else:
                    daily_qty=Decimal(row['RXQTY']/row['RXDAYS'])
                    totRemaining=Decimal(row['RXQTY']).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                    if stopDate:
                        totDays=(stopDate-startDate).days
                        if totDays==0:
                            totDays=1
                    else:
                        totDays=int(row['RXDAYS'])
                witness=daily_qty.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                if witness==int(witness):
                    witness=int(witness)

                print("======== CHECKING IF NEW/UPDATED RX ========")

                query = """SELECT * FROM rx WHERE rxID = ? and rxQty = ? and rxDays = ? and rxDin = ?"""
                paramValues = (row['RXNUM'], totRemaining, totDays, row['RXDIN'])
                local_cursor.execute(query, paramValues)
                if row['RXNUM'] == 684921:
                    print()
                rxData=dictfetchall(local_cursor)
                if rxData:
                    print("======== RX ALREADY EXISTS, NO CHANGE ========")
                    rxData=rxData[0]
                    if reDataDict.get(row['RXNUM']):
                        print("======== RE CASES EXIST FOR THE RX ========")
                        isChagingDose=rxData['isChanging']
                        query="select dose, frequency, days, cycle from cycle where rxId = ?"
                        paramValues = (row['RXNUM'],)
                        local_cursor.execute(query, paramValues)
                        cycleData=dictfetchall(local_cursor)
                        if cycleData:
                            print("======== CYCLE DATA EXISTS FOR THE RX, UPDATE REFILL FOR CYCLE ========")
                            data={
                                'localConn':localConn,
                                'loginUser':loginUser,
                                'rxData':rxData,
                                'cycleData':cycleData,
                                "reDataDict":reDataDict,
                                'checkReasonList':checkReasonList,
                                'startDate':startDate,
                                'stopDate':stopDate,
                            }
                            res=self.updateRefillForCycleData(data)
                            if res['status']=="error":
                                self.updateDispenseData.emit("error","Something went wrong",triggerBy)
                                return
                        else:
                            print("======== NO CYCLE DATA EXISTS FOR THE RX, UPDATE REFILL DEFAULT ========")
                            data={
                                'localConn':localConn,
                                'loginUser':loginUser,
                                'row':row,
                                'startDate':startDate,
                                'stopDate':stopDate,
                                'reDataDict':reDataDict,
                                'checkReasonList':checkReasonList,
                                'witness':witness,
                                'totRemaining':totRemaining,
                                'totDays':totDays,
                            }
                            res=self.updateRefillData(data)
                            if res['status']=="error":
                                self.updateDispenseData.emit("error","Something went wrong",triggerBy)
                                return
                    else:
                        print("======== NO RE CASE, NO NEED TO UPDATE REFILL ========")
                else:
                    print("======== NEW OR UPDATED RX, DELETING OLD RX DATA ========")
                    local_cursor.execute("Delete from rx where rxID = ?", row['RXNUM'])
                    
                    print("======== DELETING CYCLE DATA ========")
                    local_cursor.execute("Delete from cycle where rxId = ?", row['RXNUM'])
                    
                    print("======== INSERTING RX DATA ========")
                    query = """
                        INSERT INTO rx (rxID, patientID, rxDrug, rxOrigDate, rxStopDate, aiStartDate, aiStopDate, rxQty, rxDays, rxType, rxDin, rxSig, rxDrFirst, rxDrLast, scDays, scheduleType, rxStat, createdBy, updatedBy, createdDate, updatedDate) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    paramValues = (row['RXNUM'], row['RXPANUM'], row['RXDRUG'], row['RXORIG'], row['RXSTOP'], aiOrigDate, aiStopDate, totRemaining, totDays, row['RXTYPE'], row['RXDIN'], row['RXSIG'], row['RXDR1ST'], row['RXDRLAST'], row['SCDAYS'], scheduleType, rxStat, loginUser, loginUser, formattedcurrentDateTime, formattedcurrentDateTime)
                    local_cursor.execute(query, paramValues)

                    data={
                        'localConn':localConn,
                        'loginUser':loginUser,
                        'row':row,
                        'startDate':startDate,
                        'stopDate':stopDate,
                        'reDataDict':reDataDict,
                        'checkReasonList':checkReasonList,
                        'witness':witness,
                        'totRemaining':totRemaining,
                        'totDays':totDays,
                    }
                    res=self.updateRefillData(data)
                    if res['status']=="error":
                        self.updateDispenseData.emit("error","Something went wrong",triggerBy)
                        return
                localConn.commit()
            print("\n======== DATA UPDATED ========")
            if skippedRx:
                print("======== SKIPPED RX ========")
                print(skippedRx)
            self.updateDispenseData.emit("success","Data Synced Successfully",triggerBy)
        except Exception as e:
            print(e)
            self.updateDispenseData.emit("error","Something went wrong",triggerBy)

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, connString, userData, medidozeDir, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "settings.ui")
        uic.loadUi(ui_path, self)

        self.worker = Worker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.updateDispenseData.connect(self.responseUpdateDispenseData)

        self.config = config
        self.connString = connString
        self.userData = userData
        self.medidozeDir = medidozeDir
        self.local_conn = localConn
        self.txt_database.setText(self.config['winrxDbName'])
        self.txtOatrxPharmacyId.setText(self.config['oatRxPharmacyId'])
        self.txtWebhookUrl.setText(self.config['webhookFillApiUrl'])
        self.txtAiDateUrl.setText(self.config['oatRxGetAiDatesApiUrl'])
        self.txtApiToken.setText(self.config['oatApiToken'])

        self.loadLabelSettings()
        self.comboFontSize.setCurrentText(str(self.labelFontSize))
        if self.labelType=="normal":
            self.comboLabelType.setCurrentText("Normal Label")
            self.spinLeftMargin.setValue(self.normalLeftMargin)
            self.spinTopMargin.setValue(self.normalTopMargin)
            self.spinParaWidth.setValue(self.normalParaWidth)
            self.spinLineSpacing.setValue(self.normalLineSpacing)
            self.spinSideTextBottomMargin.setValue(self.normalSideTextBottomMargin)
        else:
            self.comboLabelType.setCurrentText("Inverted Label")
            self.spinLeftMargin.setValue(self.invertedLeftMargin)
            self.spinTopMargin.setValue(self.invertedTopMargin)
            self.spinParaWidth.setValue(self.invertedParaWidth)
            self.spinLineSpacing.setValue(self.invertedLineSpacing)
            self.spinSideTextBottomMargin.setValue(self.invertedSideTextBottomMargin)

        self.getPrinterList()
        self.selectPrinterCombo.setCurrentText(self.defaultPrinter)
        self.selectPrinterCombo.model().item(0).setEnabled(False)
        self.btnSaveOatRxSettings.clicked.connect(self.SaveOatRxSettings)
        self.comboLabelType.currentTextChanged.connect(self.changeLabelType)
        self.btnSaveLblSettings.clicked.connect(self.saveLabelSettings)
        self.btn_save_db.clicked.connect(partial(self.save_database_credential,triggerBy="Save"))
        self.frameSync.hide()
        self.err_database.setText("")
        self.txt_database.setStyleSheet("border:1px solid  #e1e4e6;font-weight: 500;padding:10px;")

    def loadLabelSettings(self):
        try:
            with open(os.path.join(self.medidozeDir, 'lblSettingsAI.json'), 'r', encoding='utf-8') as f:
                lblSettings=json.load(f)

            print("Label settings file found")
            self.defaultPrinter=lblSettings['printer']
            self.labelFontSize=lblSettings['fontSize']
            self.labelType=lblSettings['labelType']

            self.normalLeftMargin=lblSettings['normalLeftMargin']
            self.normalTopMargin=lblSettings['normalTopMargin']
            self.normalParaWidth=lblSettings['normalParaWidth']
            self.normalLineSpacing=lblSettings['normalLineSpacing']
            self.normalSideTextBottomMargin=lblSettings['normalSideTextBottomMargin']

            self.invertedLeftMargin=lblSettings['invertedLeftMargin']
            self.invertedTopMargin=lblSettings['invertedTopMargin']
            self.invertedParaWidth=lblSettings['invertedParaWidth']
            self.invertedLineSpacing=lblSettings['invertedLineSpacing']
            self.invertedSideTextBottomMargin=lblSettings['invertedSideTextBottomMargin']

        except FileNotFoundError:
            print("Label settings file not found")
            self.defaultPrinter=win32print.GetDefaultPrinter()
            self.labelFontSize=10
            self.labelType='normal'
            self.normalLeftMargin=0
            self.normalTopMargin=0
            self.normalParaWidth=260
            self.normalLineSpacing=12
            self.normalSideTextBottomMargin=50

            self.invertedLeftMargin=0
            self.invertedTopMargin=0
            self.invertedParaWidth=260
            self.invertedLineSpacing=12
            self.invertedSideTextBottomMargin=50
            lblSettings={
                'printer':self.defaultPrinter,
                'fontSize':self.labelFontSize,
                'labelType':self.labelType,

                'normalLeftMargin':self.normalLeftMargin,
                'normalTopMargin':self.normalTopMargin,
                'normalParaWidth':self.normalParaWidth,
                'normalLineSpacing':self.normalLineSpacing,
                'normalSideTextBottomMargin':self.normalSideTextBottomMargin,

                'invertedLeftMargin':self.invertedLeftMargin,
                'invertedTopMargin':self.invertedTopMargin,
                'invertedParaWidth':self.invertedParaWidth,
                'invertedLineSpacing':self.invertedLineSpacing,
                'invertedSideTextBottomMargin':self.invertedSideTextBottomMargin
            }
            with open(os.path.join(self.medidozeDir, 'lblSettingsAI.json'), 'w', encoding='utf-8') as f:
                json.dump(lblSettings, f, indent=4)
        except Exception as e:
            print(e)
            
    def getPrinterList(self):
        try:
            printers = []
            printersList=[]
            for i in range(self.selectPrinterCombo.count()):
                if i>0:
                    self.selectPrinterCombo.removeItem(1)
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                printer_info = {
                    'name': printer[2],  # Printer name
                    'port': printer[1],  # Port name
                    'description': printer[2],  # Description
                    'is_default': printer[2] == win32print.GetDefaultPrinter()  # Check if it's the default printer
                }
                printers.append(printer_info)
                printersList.append(printer[2])
                self.selectPrinterCombo.addItem(printer[2])
            
            if self.defaultPrinter and self.defaultPrinter in printersList:
                self.selectPrinterCombo.setCurrentText(self.defaultPrinter)
            print()
        except Exception as e:
            print(e)

    def SaveOatRxSettings(self):
        try:
            self.config['oatRxPharmacyId']=self.txtOatrxPharmacyId.text().strip()
            self.config['webhookFillApiUrl']=self.txtWebhookUrl.text().strip()
            self.config['oatRxGetAiDatesApiUrl']=self.txtAiDateUrl.text().strip()
            self.config['oatApiToken']=self.txtApiToken.text().strip()
            with open(os.path.join(self.medidozeDir, 'configAI.json'), 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            self.infoSettings.setText(f"OatRx settings saved successfully")
            self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            QTimer.singleShot(2000, self.clearInfoMessages)
        except Exception as e:
            print(e)

    def changeLabelType(self):
        try:
            if self.comboLabelType.currentText()=="Normal Label":
                self.spinLeftMargin.setValue(self.normalLeftMargin)
                self.spinTopMargin.setValue(self.normalTopMargin)
                self.spinParaWidth.setValue(self.normalParaWidth)
                self.spinLineSpacing.setValue(self.normalLineSpacing)
                self.spinSideTextBottomMargin.setValue(self.normalSideTextBottomMargin)
            else:
                self.spinLeftMargin.setValue(self.invertedLeftMargin)
                self.spinTopMargin.setValue(self.invertedTopMargin)
                self.spinParaWidth.setValue(self.invertedParaWidth)
                self.spinLineSpacing.setValue(self.invertedLineSpacing)
                self.spinSideTextBottomMargin.setValue(self.invertedSideTextBottomMargin)
        except Exception as e:
            print(e)

    def saveLabelSettings(self):
        try:
            self.defaultPrinter=self.selectPrinterCombo.currentText()
            self.labelFontSize=int(self.comboFontSize.currentText())
            self.labelType=("normal" if self.comboLabelType.currentText()=="Normal Label" else "inverted")
            if self.labelType=="normal":
                self.normalLeftMargin=self.spinLeftMargin.value()
                self.normalTopMargin=self.spinTopMargin.value()
                self.normalParaWidth=self.spinParaWidth.value()
                self.normalLineSpacing=self.spinLineSpacing.value()
                self.normalSideTextBottomMargin=self.spinSideTextBottomMargin.value()
            else:
                self.invertedLeftMargin=self.spinLeftMargin.value()
                self.invertedTopMargin=self.spinTopMargin.value()
                self.invertedParaWidth=self.spinParaWidth.value()
                self.invertedLineSpacing=self.spinLineSpacing.value()
                self.invertedSideTextBottomMargin=self.spinSideTextBottomMargin.value()
            lblSettings={
                'printer':self.defaultPrinter,
                'fontSize':self.labelFontSize,
                "labelType":self.labelType,
                'normalLeftMargin':self.normalLeftMargin,
                'normalTopMargin':self.normalTopMargin,
                'normalParaWidth':self.normalParaWidth,
                'normalLineSpacing':self.normalLineSpacing,
                'normalSideTextBottomMargin':self.normalSideTextBottomMargin,

                'invertedLeftMargin':self.invertedLeftMargin,
                'invertedTopMargin':self.invertedTopMargin,
                'invertedParaWidth':self.invertedParaWidth,
                'invertedLineSpacing':self.invertedLineSpacing,
                'invertedSideTextBottomMargin':self.invertedSideTextBottomMargin
            }
            with open(os.path.join(self.medidozeDir, 'lblSettingsAI.json'), 'w', encoding='utf-8') as f:
                json.dump(lblSettings, f, indent=4)
            self.infoSettings.setText(f"Label settings saved successfully")
            self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            QTimer.singleShot(2000, self.clearInfoMessages)
        except Exception as e:
            print(e)
            
    def responseUpdateDispenseData(self,status,message,triggerBy):
        try:
            self.syncMovie.stop()
            if triggerBy=="Save":
                self.frameSettingBtns.show()
                self.frameSync.hide()
                self.infoSettings.setText(message)
                self.infoSettings.show()
                if status=="success":
                    self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                    self.config['winrxDbName']=self.txt_database.text()
                    with open(os.path.join(self.medidozeDir, 'configAI.json'), 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=4)

                else:
                    self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
            else:
                self.animateLbl.hide()
                self.btnSync.show()
            QTimer.singleShot(2000, self.clearInfoMessages)
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread.disconnect()
        except Exception as e:
            print(e)

    def save_database_credential(self,triggerBy=None):
        try:
            module_dir = os.path.dirname(__file__)
            self.syncMovie = QMovie(os.path.join(module_dir, 'images', 'diagram3.gif'))
            if triggerBy=="Save":
                self.err_database.setText("")
                self.txt_database.setStyleSheet("border:1px solid  #e1e4e6;font-weight: 500;padding:10px;")
                database=self.txt_database.text()
                if str(database).strip() =="":
                    self.err_database.setText("Database name can't be blank")
                    self.txt_database.setStyleSheet("border:1px solid red;font-weight: 500;border-radius:10%;padding:10px;")
                    return
                
                self.infoSettings.setText(f"Connected to {database} database")
                self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                QTimer.singleShot(2000, self.clearInfoMessages)
                self.animateLblSettings.setMovie(self.syncMovie)
                self.frameSettingBtns.hide()
                self.frameSync.show()
            else:
                database=self.config['winrxDbName']
                self.animateLbl.setMovie(self.syncMovie)
                self.animateLbl.show()
                self.btnSync.hide()
            try:
                live_db = f'DRIVER={{SQL Server}};SERVER={self.config['server']};DATABASE={database};UID={self.config['username']};PWD={self.config['password']};'
                self.live_conn = pyodbc.connect(live_db)
                self.syncMovie.start()
                self.worker.count=0
                self.worker_thread.start()
                self.worker_thread.started.connect(partial(self.worker.update_dispense_data,self.local_conn,self.live_conn,self.userData['uid'],triggerBy,self.config['oatRxGetAiDatesApiUrl'],self.config['oatRxPharmacyId'],self.config['oatApiToken']))
            except Exception as e:
                self.syncMovie.stop()
                self.frameSettingBtns.show()
                self.frameSync.hide()
                print("Error connecting to SQL Server:", e)
                self.infoSettings.setText(f"Error connecting to {database} database")
                self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
                # self.infoViewDispense.show()
                # self.infoViewDispense.setText(f"Error connecting to database")
                # self.infoViewDispense.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
                return
            print("updated")
        except Exception as e:
            print(e)

    def clearInfoMessages(self):
        self.infoSettings.setText("")
        self.infoSettings.setStyleSheet("background:none")

