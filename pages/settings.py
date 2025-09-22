# pages/settings_page.py
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import os, pyodbc, win32print, json, requests
from functools import partial
from datetime import datetime, timedelta
from otherFiles.common import dictfetchall,medidozeDir
from decimal import Decimal, ROUND_DOWN


class Worker(QThread):
    updateDispenseData = pyqtSignal(str, str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.count = 0

    def processRefillData(self, data):
        """Consolidated method to handle all refill data processing"""
        try:
            localConn = data['localConn']
            localCursor = localConn.cursor()
            loginUser = data['loginUser']
            checkReasonList = data['checkReasonList']
            reDataDict = data['reDataDict']
            stopDate = data['stopDate']
            reefDate = data['startDate']

            rxData = data.get('rxData', {})
            row = data.get('row', {})
            
            # Extract common data
            rxId = rxData.get('rxID', row.get('RXNUM'))
            patientId = rxData.get('patientID', row.get('RXPANUM'))
            scheduleType = rxData.get('scheduleType', self.determineScheduleType(row.get('SCDAYS')))
            totalRemaining = rxData.get('rxQty', data.get('totRemaining', 0))
            carryEnabled = rxData.get('carryEnabled', 'N')
            witness = data.get('witness', 0)
            totalDays = data.get('totDays', 0)

            # Delete existing refill data
            localCursor.execute(f"DELETE FROM refill WHERE rxId = {rxId}")

            # Process based on schedule type
            if scheduleType == "Daily":
                self.processDailySchedule(localCursor, rxId, patientId, reefDate, stopDate, 
                                        witness, totalRemaining, loginUser, reDataDict, checkReasonList)
            elif scheduleType in ("Changing", "Weekly", "Custom"):
                self.processCustomSchedule(localCursor, rxId, patientId, reefDate, stopDate, 
                                         witness, totalRemaining, loginUser, reDataDict, checkReasonList, 
                                         data.get('cycleData', []), carryEnabled, totalDays, row.get('SCDAYS'))
            elif scheduleType == 'EOD':
                self.processEodSchedule(localCursor, rxId, patientId, reefDate, stopDate, 
                                      witness, totalRemaining, loginUser, reDataDict, checkReasonList, 
                                      data.get('cycleData', []), carryEnabled)

            # Add emergency refills
            self.addEmergencyRefills(localCursor, rxId, patientId, reefDate, witness, loginUser)
            
            return {"status": "success"}
        except Exception as e:
            print("Error:", e)
            return {"status": "error", "message": str(e)}

    def determineScheduleType(self, scDays):
        """Determine schedule type based on SCDAYS"""
        if not scDays or len(str(scDays).strip()) in (0, 7):
            return 'Daily'
        return 'New'

    def processDailySchedule(self, cursor, rxId, patientId, reefDate, stopDate, witness, 
                           totalRemaining, loginUser, reDataDict, checkReasonList):
        """Process daily schedule refills"""
        print("======== DAILY SCHEDULE ========")
        prevDate = None
        emergencyCount = 0
        
        while totalRemaining > 0:
            if stopDate and reefDate > stopDate:
                print("refill stopped due to stop date")
                break
                
            totalProcessing = witness
            totalRemaining -= totalProcessing
            reReason = reDataDict.get(rxId, {}).get(reefDate.date(), None)
            if reReason not in checkReasonList:
                reReason = None
                
            self.insertRefillRecord(cursor, rxId, patientId, reefDate, prevDate, witness, 
                                  "0", 1, emergencyCount, totalProcessing, totalRemaining, 
                                  reReason, loginUser)
            
            if reReason:
                totalRemaining += totalProcessing
            else:
                prevDate = reefDate
            reefDate += timedelta(days=1)

    def processCustomSchedule(self, cursor, rxId, patientId, reefDate, stopDate, witness, 
                            totalRemaining, loginUser, reDataDict, checkReasonList, 
                            cycleData, carryEnabled, totalDays, scDays):
        """Process custom schedule refills"""
        print("======== CUSTOM SCHEDULE ========")
        customCycleData = self.buildCustomCycleData(cycleData)
        resArr = self.buildScheduleArray(scDays, totalDays, reefDate)
        
        prevDate = None
        emergencyCount = 0
        
        for cycle, cycleData in customCycleData.items():
            if stopDate and reefDate > stopDate:
                break
                
            dayVal = cycleData['days']
            doseArr = cycleData['doseArr']
            frequency = cycleData['frequency']
            
            witnessVal = float(doseArr[0])
            witness = int(witnessVal) if witnessVal.is_integer() else witnessVal
            
            dayCarry = sum(float(d) for d in doseArr[1:]) if len(doseArr) > 1 else 0
            dayCarryStr = ",".join(doseArr[1:]) if len(doseArr) > 1 else "0"
            
            loop = 0
            while loop < dayVal and totalRemaining > 0:
                if stopDate and reefDate > stopDate:
                    break
                    
                item = resArr[0] if resArr else 1
                if item:
                    carry, carryStr = self.calculateCarry(item, witness, dayCarry, dayCarryStr, carryEnabled)
                    totalProcessing = witness + carry
                    totalRemaining -= totalProcessing
                    
                    reReason = reDataDict.get(rxId, {}).get(reefDate.date(), None)
                    if reReason not in checkReasonList:
                        reReason = None
                        
                    self.insertRefillRecord(cursor, rxId, patientId, reefDate, prevDate, witness, 
                                          carryStr, frequency, emergencyCount, totalProcessing, 
                                          totalRemaining, reReason, loginUser)
                    
                    if reReason:
                        totalRemaining += totalProcessing
                    else:
                        prevDate = reefDate
                        loop += 1
                        if resArr:
                            resArr.pop(0)
                reefDate += timedelta(days=1)

    def processEodSchedule(self, cursor, rxId, patientId, reefDate, stopDate, witness, 
                         totalRemaining, loginUser, reDataDict, checkReasonList, 
                         cycleData, carryEnabled):
        """Process EOD schedule refills"""
        print("======== EOD SCHEDULE ========")
        customCycleData = self.buildCustomCycleData(cycleData)
        
        prevDate = None
        emergencyCount = 0
        
        for cycle, cycleData in customCycleData.items():
            if stopDate and reefDate > stopDate:
                break
                
            dayVal = cycleData['days']
            doseArr = cycleData['doseArr']
            frequency = cycleData['frequency']
            
            witnessVal = float(doseArr[0])
            witness = int(witnessVal) if witnessVal.is_integer() else witnessVal
            
            dayCarry = sum(float(d) for d in doseArr[1:]) if len(doseArr) > 1 else 0
            dayCarryStr = ",".join(doseArr[1:]) if len(doseArr) > 1 else "0"
            
            loop = 0
            while loop < dayVal and totalRemaining > 0:
                if stopDate and reefDate > stopDate:
                    break
                    
                if loop % 2 == 0:
                    carry = witness + (dayCarry * 2) if dayCarry > 0 else witness
                    carryStr = f"{dayCarryStr},{witness},{dayCarryStr}" if dayCarry > 0 else str(witness)
                else:
                    carry = 0
                    carryStr = "0"
                    
                totalProcessing = witness + carry
                totalRemaining -= totalProcessing
                
                reReason = reDataDict.get(rxId, {}).get(reefDate.date(), None)
                if reReason not in checkReasonList:
                    reReason = None
                    
                self.insertRefillRecord(cursor, rxId, patientId, reefDate, prevDate, witness, 
                                      carryStr, frequency, emergencyCount, totalProcessing, 
                                      totalRemaining, reReason, loginUser)
                
                if reReason:
                    totalRemaining += totalProcessing
                else:
                    prevDate = reefDate
                    loop += 1
                reefDate += timedelta(days=2)

    def buildCustomCycleData(self, cycleData):
        """Build custom cycle data structure"""
        customCycleData = {}
        for row in cycleData:
            row['dose'] = str(int(row['dose'])) if row['dose'].is_integer() else str(row['dose'])
            if row['cycle'] not in customCycleData:
                customCycleData[row['cycle']] = {
                    'frequency': row['frequency'],
                    'days': row['days'],
                    'doseArr': [row['dose']]
                }
            else:
                customCycleData[row['cycle']]['doseArr'].append(row['dose'])
        return customCycleData

    def buildScheduleArray(self, scDays, totalDays, startDate):
        """Build schedule array for custom schedules"""
        if not scDays or len(str(scDays).strip()) in (0, 7):
            return [1] * totalDays
            
        weekDay = startDate.weekday() + 1
        resStr = ""
        for i in range(weekDay, totalDays + weekDay):
            char = scDays[i % len(scDays)]
            resStr += str(char)
            
        resArr = []
        prevInd = ""
        count = 1
        firstDay = False
        lastInd = totalDays - 1
        
        for ind, i in enumerate(resStr):
            if i == " " and ind == 0:
                firstDay = True
                resArr.append(1)
                prevInd = ind
            elif i == " " and ind == lastInd:
                if prevInd == "":
                    prevInd = ind - 1
                count += 1
                resArr[prevInd] = 1 * count
                resArr.append("")
            elif i == " ":
                if prevInd == "":
                    prevInd = ind - 1
                count += 1
                resArr.append("")
            else:
                if firstDay:
                    resArr[prevInd] = 1 * count
                    prevInd = ind
                    firstDay = False
                else:
                    if prevInd != "":
                        resArr[prevInd] = 1 * count
                        prevInd = ""
                resArr.append(1)
                count = 1
        return resArr

    def calculateCarry(self, item, witness, dayCarry, dayCarryStr, carryEnabled):
        """Calculate carry values"""
        if carryEnabled == "N":
            item = 1
            
        if item == 1 and dayCarry > 0:
            return dayCarry, dayCarryStr
        elif item > 1:
            if dayCarry == 0:
                carry = witness * (item - 1)
                carryStr = (',' + str(witness)) * (item - 1)
                carryStr = carryStr[1:]
            else:
                carry = ((witness + dayCarry) * item) - witness
                carryStr = dayCarryStr + (',' + str(witness) + ',' + dayCarryStr) * (item - 1)
            return carry, carryStr
        return 0, "0"

    def insertRefillRecord(self, cursor, rxId, patientId, reefDate, prevDate, witness, 
                          carryStr, frequency, emergencyCount, totalProcessing, totalRemaining, 
                          reReason, loginUser):
        """Insert refill record into database"""
        print("-- UPDATING REFILL FOR DATE: ", reefDate.date())
        
        if prevDate:
            query = """INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, 
                        frequency, emergencyCount, totProcessing, totRemaining, reReason, 
                        createdBy, updatedBy, createdDate, updatedDate) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            params = (rxId, patientId, reefDate, prevDate, witness, carryStr, frequency, 
                     emergencyCount, totalProcessing, totalRemaining, reReason, loginUser, 
                     loginUser, datetime.now(), datetime.now())
        else:
            query = """INSERT INTO refill (rxID, patientID, reefDate, witness, carry, 
                        frequency, emergencyCount, totProcessing, totRemaining, reReason, 
                        createdBy, updatedBy, createdDate, updatedDate) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            params = (rxId, patientId, reefDate, witness, carryStr, frequency, emergencyCount, 
                     totalProcessing, totalRemaining, reReason, loginUser, loginUser, 
                     datetime.now(), datetime.now())
        cursor.execute(query, params)

    def addEmergencyRefills(self, cursor, rxId, patientId, reefDate, witness, loginUser):
        """Add emergency refill records"""
        for _ in range(15):
            emergencyCount = _ + 1
            carryStr = "0"
            totalRemaining = 0
            totalProcessing = witness
            query = """INSERT INTO refill (rxID, patientID, reefDate, prevDate, witness, carry, 
                        emergencyCount, totProcessing, totRemaining, createdBy, updatedBy, 
                        createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            params = (rxId, patientId, reefDate, reefDate, witness, carryStr, emergencyCount, 
                     totalProcessing, totalRemaining, loginUser, loginUser, datetime.now(), 
                     datetime.now())
            cursor.execute(query, params)
            reefDate += timedelta(days=1)

    def syncDispenseData(self, localConn, liveConn, loginUser, triggerBy, getDateApiUrl, 
                          pharmacyId, apiToken):
        """Consolidated method to update dispense data"""
        try:
            localCursor = localConn.cursor()
            medicationArr = self.getMedicationArray(localCursor)
            checkReasonList = ['RE', 'RU', 'RR', 'RC']
            
            if not medicationArr:
                self.updateDispenseData.emit("success", "Medication not found", triggerBy)
                return
                
            reqDin = self.getRequiredDins(localCursor, medicationArr)
            currentDateTime = datetime.now()
            currentDateTime = datetime(2025, 9, 7)
            formattedDateTime = currentDateTime.strftime('%Y-%m-%d %H:%M:%S')
            
            liveCursor = liveConn.cursor()
            todayRxData = self.getTodayRxData(liveCursor, reqDin, formattedDateTime)
            if not todayRxData:
                self.updateDispenseData.emit("success", "No Rx found in winrx database for today", triggerBy)
                return
                
            rxList = [int(row['RERXNUM']) for row in todayRxData]
            reDataDict = self.buildReDataDict(liveCursor, rxList)
            
            rxPatientData = self.getRxPatientData(liveCursor, rxList)
            self.processRxData(localCursor, rxPatientData, reDataDict, checkReasonList, 
                             loginUser, formattedDateTime, localConn)
            
            print("\n======== DATA UPDATED ========")
            self.updateDispenseData.emit("success", "Data Synced Successfully", triggerBy)
        except Exception as e:
            print(e)
            self.updateDispenseData.emit("error", "Something went wrong", triggerBy)

    def getMedicationArray(self, cursor):
        """Get medication array from din_groups"""
        cursor.execute("SELECT * FROM din_groups")
        return [med['medication'] for med in dictfetchall(cursor)]

    def getRequiredDins(self, cursor, medicationArr):
        """Get required DINs for medications"""
        formatMedication = f"('{medicationArr[0]}')" if len(medicationArr) == 1 else tuple(medicationArr)
        query = f"SELECT din_number from din join din_groups on din.din_group_id=din_groups.id where medication IN {formatMedication}"
        cursor.execute(query)
        return [value[0] for value in cursor.fetchall()]

    def getTodayRxData(self, cursor, reqDin, formattedDateTime):
        """Get today's RX data"""
        query = f"select RERXNUM, REREASON from refill where REDIN IN {tuple(reqDin)} AND CONVERT(date,REEFDATE)='{formattedDateTime}'"
        cursor.execute(query)
        return dictfetchall(cursor)

    def buildReDataDict(self, cursor, rxList):
        """Build RE data dictionary"""
        reDataDict = {}
        formatRxList = f"({rxList[0]})" if len(rxList) == 1 else tuple(rxList)
        query = f"select RERXNUM, REEFDATE, REREASON from refill where RERXNUM IN {formatRxList} and reReason is not null"
        cursor.execute(query)
        reData = dictfetchall(cursor)
        
        for dt in reData:
            reReefDate = dt['REEFDATE'].date()
            reRxNum = int(dt['RERXNUM'])
            reReason = dt['REREASON']
            if reRxNum not in reDataDict:
                reDataDict[reRxNum] = {reReefDate: reReason}
            else:
                reDataDict[reRxNum][reReefDate] = reReason
        return reDataDict

    def getRxPatientData(self, cursor, rxList):
        """Get RX and patient data"""
        formatRxList = f"({rxList[0]})" if len(rxList) == 1 else tuple(rxList)
        query = f"""select patient.PAROUTE, patient.PAGIVEN, patient.PASURNAME, patient.PASEX, 
                   patient.PAAREA, patient.PAPHONE, RXNUM, RX.RXPANUM, RX.RXTYPE, RX.RXSIG, 
                   RX.RXDR1ST, RX.RXDRLAST, RX.RXDIN, RX.RXORIG, RX.RXSTOP, RX.RXQTY, RX.RXDAYS, 
                   RX.RXLIM, RX.RXDRUG, RX.RXSTAT, RX.RXNOTE, SCHEDULE.SCDAYS 
                   from RX JOIN patient ON patient.PANUM = RX.RXPANUM 
                   LEFT JOIN SCHEDULE ON RX.RXNUM=SCHEDULE.SCRXNUM 
                   where RX.RXNUM IN {formatRxList} ORDER BY RX.RXNUM"""
        cursor.execute(query)
        return dictfetchall(cursor)

    def processRxData(self, cursor, rxPatientData, reDataDict, checkReasonList, 
                     loginUser, formattedDateTime, localConn):
        """Process RX data and update database"""
        skippedRx = {}
        
        for row in rxPatientData:
            print(f"\n========================= PROCESSING RX: {int(row['RXNUM'])} ==========================")
            
            startDate = self.determineStartDate(row)
            if not startDate:
                skippedRx[row['RXNUM']] = "Don't get start date"
                continue
                
            self.updatePatientData(cursor, row, loginUser, formattedDateTime)
            
            stopDate = self.determineStopDate(row)
            rxStat = self.determineRxStatus(row, stopDate)
            scheduleType = self.determineScheduleType(row['SCDAYS'])
            
            witness, totalRemaining, totalDays = self.calculateRxValues(row, startDate, stopDate)
            
            existingRx = self.checkExistingRx(cursor, row, totalRemaining, totalDays)
            
            if existingRx:
                self.handleExistingRx(cursor, row, existingRx, reDataDict, checkReasonList, 
                                    startDate, stopDate, witness, totalRemaining, totalDays, 
                                    loginUser, localConn)
            else:
                self.handleNewRx(cursor, row, startDate, stopDate, witness, totalRemaining, 
                               totalDays, rxStat, scheduleType, loginUser, formattedDateTime, 
                               localConn, reDataDict, checkReasonList)
            
            localConn.commit()

    def determineStartDate(self, row):
        """Determine start date for RX"""
        if row['RXORIG']:
            return row['RXORIG']
        return None

    def determineStopDate(self, row):
        """Determine stop date for RX"""
        return row['RXSTOP'] if row['RXSTOP'] else None

    def determineRxStatus(self, row, stopDate):
        """Determine RX status"""
        rxStat = row['RXSTAT']
        if stopDate and datetime.now().date() >= stopDate.date():
            rxStat = 'S'
            if str(row['RXNOTE']).startswith('->'):
                rxStat = 'Tsf'
        return rxStat

    def calculateRxValues(self, row, startDate, stopDate):
        """Calculate RX values"""
        if row['RXLIM'] > 0:
            dailyQty = Decimal(row['RXQTY'])
            totalDays = int(row['RXLIM']) + 1
            totalRemaining = Decimal(row['RXQTY'] * totalDays).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        else:
            dailyQty = Decimal(row['RXQTY'] / row['RXDAYS'])
            totalRemaining = Decimal(row['RXQTY']).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            if stopDate:
                totalDays = (stopDate - startDate).days
                if totalDays == 0:
                    totalDays = 1
            else:
                totalDays = int(row['RXDAYS'])
                
        witness = dailyQty.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        if witness == int(witness):
            witness = int(witness)
        return witness, totalRemaining, totalDays

    def checkExistingRx(self, cursor, row, totalRemaining, totalDays):
        """Check if RX already exists"""
        query = "SELECT * FROM rx WHERE rxID = ? and rxQty = ? and rxDays = ? and rxDin = ?"
        params = (row['RXNUM'], totalRemaining, totalDays, row['RXDIN'])
        cursor.execute(query, params)
        result = dictfetchall(cursor)
        return result[0] if result else None

    def updatePatientData(self, cursor, row, loginUser, formattedDateTime):
        """Update patient data"""
        phone = str(row['PAPHONE']).replace('-', '')
        query = """IF EXISTS (SELECT 1 FROM patient WHERE id = ?)
                   UPDATE patient SET route = ?, firstName = ?, lastName = ?, gender = ?, 
                   areaCode = ?, phone = ?, updatedBy = ?, updatedDate = ? WHERE id = ?
                   ELSE
                   INSERT INTO patient (id, route, firstName, lastName, gender, areaCode, phone, 
                   createdBy, updatedBy, createdDate, updatedDate) VALUES (?,?,?,?,?,?,?,?,?,?,?)"""
        params = (row['RXPANUM'], row['PAROUTE'], row['PAGIVEN'], row['PASURNAME'], 
                 row['PASEX'], row['PAAREA'], phone, loginUser, formattedDateTime, row['RXPANUM'], 
                 row['RXPANUM'], row['PAROUTE'], row['PAGIVEN'], row['PASURNAME'], row['PASEX'], 
                 row['PAAREA'], phone, loginUser, loginUser, formattedDateTime, formattedDateTime)
        cursor.execute(query, params)

    def handleExistingRx(self, cursor, row, existingRx, reDataDict, checkReasonList, 
                        startDate, stopDate, witness, totalRemaining, totalDays, loginUser, localConn):
        """Handle existing RX"""
        print("======== RX ALREADY EXISTS, NO CHANGE ========")
        if reDataDict.get(row['RXNUM']):
            print("======== RE CASES EXIST FOR THE RX ========")
            cycleData = self.getCycleData(cursor, row['RXNUM'])
            if cycleData:
                print("======== CYCLE DATA EXISTS FOR THE RX, UPDATE REFILL FOR CYCLE ========")
                data = {
                    'localConn': localConn,
                    'loginUser': loginUser,
                    'rxData': existingRx,
                    'cycleData': cycleData,
                    "reDataDict": reDataDict,
                    'checkReasonList': checkReasonList,
                    'startDate': startDate,
                    'stopDate': stopDate,
                }
                self.processRefillData(data)
            else:
                print("======== NO CYCLE DATA EXISTS FOR THE RX, UPDATE REFILL DEFAULT ========")
                data = {
                    'localConn': localConn,
                    'loginUser': loginUser,
                    'row': row,
                    'startDate': startDate,
                    'stopDate': stopDate,
                    'reDataDict': reDataDict,
                    'checkReasonList': checkReasonList,
                    'witness': witness,
                    'totRemaining': totalRemaining,
                    'totDays': totalDays,
                }
                self.processRefillData(data)
        else:
            print("======== NO RE CASE, NO NEED TO UPDATE REFILL ========")

    def handleNewRx(self, cursor, row, startDate, stopDate, witness, totalRemaining, 
                   totalDays, rxStat, scheduleType, loginUser, formattedDateTime, 
                   localConn, reDataDict, checkReasonList):
        """Handle new RX"""
        print("======== NEW OR UPDATED RX, DELETING OLD RX DATA ========")
        cursor.execute("Delete from rx where rxID = ?", row['RXNUM'])
        cursor.execute("Delete from cycle where rxId = ?", row['RXNUM'])
        
        print("======== INSERTING RX DATA ========")
        query = """INSERT INTO rx (rxID, patientID, rxDrug, rxOrigDate, rxStopDate, aiStartDate, 
                    aiStopDate, rxQty, rxDays, rxType, rxDin, rxSig, rxDrFirst, rxDrLast, 
                    scDays, scheduleType, rxStat, createdBy, updatedBy, createdDate, updatedDate) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (row['RXNUM'], row['RXPANUM'], row['RXDRUG'], row['RXORIG'], row['RXSTOP'], 
                 None, None, totalRemaining, totalDays, row['RXTYPE'], row['RXDIN'], row['RXSIG'], 
                 row['RXDR1ST'], row['RXDRLAST'], row['SCDAYS'], scheduleType, rxStat, 
                 loginUser, loginUser, formattedDateTime, formattedDateTime)
        cursor.execute(query, params)
        
        data = {
            'localConn': localConn,
            'loginUser': loginUser,
            'row': row,
            'startDate': startDate,
            'stopDate': stopDate,
            'reDataDict': reDataDict,
            'checkReasonList': checkReasonList,
            'witness': witness,
            'totRemaining': totalRemaining,
            'totDays': totalDays,
        }
        self.processRefillData(data)

    def getCycleData(self, cursor, rxId):
        """Get cycle data for RX"""
        query = "select dose, frequency, days, cycle from cycle where rxId = ?"
        cursor.execute(query, (rxId,))
        return dictfetchall(cursor)

class SettingsWindow(QWidget):
    # Signal to notify main app when WinRx is configured
    winRxConfigured = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
            
        self.rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(self.rootDir, "uiFiles", "settings.ui")
        uic.loadUi(ui_path, self)

        # Initialize worker and thread as None - will be created when needed
        self.worker = None
        self.workerThread = None

        self.config = config
        self.userData = userData
        self.medidozeDir = medidozeDir
        self.localConn = localConn
        
        self.initializeSettings()
        self.setupConnections()

    def initializeSettings(self):
        """Initialize all settings"""
        self.txtDatabase.setText(self.config['winrxDbName'])
        self.txtOatrxPharmacyId.setText(self.config['oatRxPharmacyId'])
        self.txtWebhookUrl.setText(self.config['webhookFillApiUrl'])
        self.txtAiDateUrl.setText(self.config['oatRxGetAiDatesApiUrl'])
        self.txtApiToken.setText(self.config['oatApiToken'])

        self.loadLabelSettings()
        self.comboFontSize.setCurrentText(str(self.labelFontSize))
        self.setLabelTypeSettings()
        self.getPrinterList()
        self.selectPrinterCombo.setCurrentText(self.defaultPrinter)
        self.selectPrinterCombo.model().item(0).setEnabled(False)
        
        self.frameSync.hide()
        self.errDatabase.setText("")
        self.txtDatabase.setStyleSheet("border:1px solid  #e1e4e6;font-weight: 500;padding:10px;")

    def setupConnections(self):
        """Setup button connections"""
        self.btnSaveOatRxSettings.clicked.connect(self.saveOatRxSettings)
        self.comboLabelType.currentTextChanged.connect(self.changeLabelType)
        self.btnSaveLblSettings.clicked.connect(self.saveLabelSettings)
        self.btnSaveDb.clicked.connect(partial(self.saveDatabaseCredential, triggerBy="Save"))

    def createWorkerAndThread(self):
        """Create new worker and thread for each sync operation"""
        # Clean up existing worker and thread if they exist
        if self.workerThread and self.workerThread.isRunning():
            self.cleanupWorker()
        
        # Create new worker and thread
        self.worker = Worker()
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)
        self.worker.updateDispenseData.connect(self.responseUpdateDispenseData)

    def setLabelTypeSettings(self):
        """Set label type specific settings"""
        if self.labelType == "normal":
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

    def loadLabelSettings(self):
        """Load label settings from file"""
        try:
            with open(os.path.join(self.medidozeDir, 'lblSettingsAI.json'), 'r', encoding='utf-8') as f:
                lblSettings = json.load(f)

            print("Label settings file found")
            self.defaultPrinter = lblSettings['printer']
            self.labelFontSize = lblSettings['fontSize']
            self.labelType = lblSettings['labelType']

            self.normalLeftMargin = lblSettings['normalLeftMargin']
            self.normalTopMargin = lblSettings['normalTopMargin']
            self.normalParaWidth = lblSettings['normalParaWidth']
            self.normalLineSpacing = lblSettings['normalLineSpacing']
            self.normalSideTextBottomMargin = lblSettings['normalSideTextBottomMargin']

            self.invertedLeftMargin = lblSettings['invertedLeftMargin']
            self.invertedTopMargin = lblSettings['invertedTopMargin']
            self.invertedParaWidth = lblSettings['invertedParaWidth']
            self.invertedLineSpacing = lblSettings['invertedLineSpacing']
            self.invertedSideTextBottomMargin = lblSettings['invertedSideTextBottomMargin']

        except FileNotFoundError:
            print("Label settings file not found")
            self.setDefaultLabelSettings()
            self.saveDefaultLabelSettings()

    def setDefaultLabelSettings(self):
        """Set default label settings"""
        self.defaultPrinter = win32print.GetDefaultPrinter()
        self.labelFontSize = 10
        self.labelType = 'normal'
        self.normalLeftMargin = 0
        self.normalTopMargin = 0
        self.normalParaWidth = 260
        self.normalLineSpacing = 12
        self.normalSideTextBottomMargin = 50
        self.invertedLeftMargin = 0
        self.invertedTopMargin = 0
        self.invertedParaWidth = 260
        self.invertedLineSpacing = 12
        self.invertedSideTextBottomMargin = 50

    def saveDefaultLabelSettings(self):
        """Save default label settings to file"""
        lblSettings = {
            'printer': self.defaultPrinter,
            'fontSize': self.labelFontSize,
            'labelType': self.labelType,
            'normalLeftMargin': self.normalLeftMargin,
            'normalTopMargin': self.normalTopMargin,
            'normalParaWidth': self.normalParaWidth,
            'normalLineSpacing': self.normalLineSpacing,
            'normalSideTextBottomMargin': self.normalSideTextBottomMargin,
            'invertedLeftMargin': self.invertedLeftMargin,
            'invertedTopMargin': self.invertedTopMargin,
            'invertedParaWidth': self.invertedParaWidth,
            'invertedLineSpacing': self.invertedLineSpacing,
            'invertedSideTextBottomMargin': self.invertedSideTextBottomMargin
        }
        with open(os.path.join(self.medidozeDir, 'lblSettingsAI.json'), 'w', encoding='utf-8') as f:
            json.dump(lblSettings, f, indent=4)

    def getPrinterList(self):
        """Get list of available printers"""
        try:
            for i in range(self.selectPrinterCombo.count()):
                if i > 0:
                    self.selectPrinterCombo.removeItem(1)
                    
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                self.selectPrinterCombo.addItem(printer[2])
            
            if self.defaultPrinter:
                self.selectPrinterCombo.setCurrentText(self.defaultPrinter)
        except Exception as e:
            print(e)

    def saveOatRxSettings(self):
        """Save OatRx settings"""
        try:
            self.config['oatRxPharmacyId'] = self.txtOatrxPharmacyId.text().strip()
            self.config['webhookFillApiUrl'] = self.txtWebhookUrl.text().strip()
            self.config['oatRxGetAiDatesApiUrl'] = self.txtAiDateUrl.text().strip()
            self.config['oatApiToken'] = self.txtApiToken.text().strip()
            
            with open(os.path.join(self.medidozeDir, 'configAI.json'), 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
                
            self.showInfoMessage("OatRx settings saved successfully", "success")
        except Exception as e:
            print(e)

    def changeLabelType(self):
        """Change label type and update settings"""
        try:
            if self.comboLabelType.currentText() == "Normal Label":
                self.updateLabelSettings(self.normalLeftMargin, self.normalTopMargin, 
                                       self.normalParaWidth, self.normalLineSpacing, 
                                       self.normalSideTextBottomMargin)
            else:
                self.updateLabelSettings(self.invertedLeftMargin, self.invertedTopMargin, 
                                       self.invertedParaWidth, self.invertedLineSpacing, 
                                       self.invertedSideTextBottomMargin)
        except Exception as e:
            print(e)

    def updateLabelSettings(self, leftMargin, topMargin, paraWidth, lineSpacing, sideTextBottomMargin):
        """Update label settings in UI"""
        self.spinLeftMargin.setValue(leftMargin)
        self.spinTopMargin.setValue(topMargin)
        self.spinParaWidth.setValue(paraWidth)
        self.spinLineSpacing.setValue(lineSpacing)
        self.spinSideTextBottomMargin.setValue(sideTextBottomMargin)

    def saveLabelSettings(self):
        """Save label settings"""
        try:
            self.defaultPrinter = self.selectPrinterCombo.currentText()
            self.labelFontSize = int(self.comboFontSize.currentText())
            self.labelType = "normal" if self.comboLabelType.currentText() == "Normal Label" else "inverted"
            
            if self.labelType == "normal":
                self.normalLeftMargin = self.spinLeftMargin.value()
                self.normalTopMargin = self.spinTopMargin.value()
                self.normalParaWidth = self.spinParaWidth.value()
                self.normalLineSpacing = self.spinLineSpacing.value()
                self.normalSideTextBottomMargin = self.spinSideTextBottomMargin.value()
            else:
                self.invertedLeftMargin = self.spinLeftMargin.value()
                self.invertedTopMargin = self.spinTopMargin.value()
                self.invertedParaWidth = self.spinParaWidth.value()
                self.invertedLineSpacing = self.spinLineSpacing.value()
                self.invertedSideTextBottomMargin = self.spinSideTextBottomMargin.value()
                
            self.saveLabelSettingsToFile()
            self.showInfoMessage("Label settings saved successfully", "success")
        except Exception as e:
            print(e)

    def saveLabelSettingsToFile(self):
        """Save label settings to file"""
        lblSettings = {
            'printer': self.defaultPrinter,
            'fontSize': self.labelFontSize,
            "labelType": self.labelType,
            'normalLeftMargin': self.normalLeftMargin,
            'normalTopMargin': self.normalTopMargin,
            'normalParaWidth': self.normalParaWidth,
            'normalLineSpacing': self.normalLineSpacing,
            'normalSideTextBottomMargin': self.normalSideTextBottomMargin,
            'invertedLeftMargin': self.invertedLeftMargin,
            'invertedTopMargin': self.invertedTopMargin,
            'invertedParaWidth': self.invertedParaWidth,
            'invertedLineSpacing': self.invertedLineSpacing,
            'invertedSideTextBottomMargin': self.invertedSideTextBottomMargin
        }
        with open(os.path.join(self.medidozeDir, 'lblSettingsAI.json'), 'w', encoding='utf-8') as f:
            json.dump(lblSettings, f, indent=4)

    def responseUpdateDispenseData(self, status, message, triggerBy):
        """Handle response from dispense data update"""
        try:
            self.syncMovie.stop()
            if triggerBy == "Save":
                self.frameSettingBtns.show()
                self.frameSync.hide()
                self.infoSettings.setText(message)
                self.infoSettings.show()
                if status == "success":
                    self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                    self.config['winrxDbName'] = self.txtDatabase.text()
                    with open(os.path.join(self.medidozeDir, 'configAI.json'), 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=4)

                    self.winRxConfigured.emit()
                else:
                    self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
            else:
                # For non-Save operations, just show the message
                self.infoSettings.setText(message)
                self.infoSettings.show()
                if status == "success":
                    self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                else:
                    self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
                
            QTimer.singleShot(2000, self.clearInfoMessages)
            self.cleanupWorker()
        except Exception as e:
            print(f"Error in responseUpdateDispenseData: {e}")

    def cleanupWorker(self):
        """Clean up worker thread"""
        if self.workerThread and self.workerThread.isRunning():
            self.workerThread.quit()
            self.workerThread.wait(3000)  # Wait up to 3 seconds
            
        if self.worker:
            try:
                self.worker.updateDispenseData.disconnect()
            except TypeError:
                pass
            self.worker.deleteLater()
            self.worker = None
            
        if self.workerThread:
            try:
                self.workerThread.started.disconnect()
            except TypeError:
                pass
            self.workerThread.deleteLater()
            self.workerThread = None

    def saveDatabaseCredential(self, triggerBy=None):
        """Save database credentials and sync"""
        try:
            reply = QMessageBox.warning(self, 'Medidoze alert',
                                      f"This will save the database credential and sync with winrx database. Do you want to proceed ?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
                
            self.syncMovie = QMovie(os.path.join(self.rootDir, 'images', 'diagram3.gif'))
            
            if triggerBy == "Save":
                if not self.validateDatabaseInput():
                    return
                self.setupSyncUI()
            else:
                # For non-Save operations, just show the sync animation
                self.animateLblSettings.setMovie(self.syncMovie)
                self.animateLblSettings.show()
                
            self.connectToDatabaseAndSync(triggerBy)
        except Exception as e:
            print(f"Error in saveDatabaseCredential: {e}")

    def validateDatabaseInput(self):
        """Validate database input"""
        try:
            self.errDatabase.setText("")
            self.txtDatabase.setStyleSheet("border:1px solid  #e1e4e6;font-weight: 500;padding:10px;")
            database = self.txtDatabase.text()
            if str(database).strip() == "":
                self.errDatabase.setText("Database name can't be blank")
                self.txtDatabase.setStyleSheet("border:1px solid red;font-weight: 500;border-radius:10%;padding:10px;")
                return False
            return True
        except Exception as e:
            print(f"Error in validateDatabaseInput: {e}")
            return False

    def setupSyncUI(self):
        """Setup sync UI"""
        try:
            database = self.txtDatabase.text()
            self.showInfoMessage(f"Connected to {database} database", "success")
            self.animateLblSettings.setMovie(self.syncMovie)
            self.frameSettingBtns.hide()
            self.frameSync.show()
        except Exception as e:
            print(f"Error in setup Sync UI: {e}")

    def connectToDatabaseAndSync(self, triggerBy):
        """Connect to database and start sync"""
        try:
            # Create new worker and thread for each sync
            self.createWorkerAndThread()
            
            database = self.txtDatabase.text() if triggerBy == "Save" else self.config['winrxDbName']
            liveDb = f'DRIVER={{SQL Server}};SERVER={self.config["server"]};DATABASE={database};UID={self.config["username"]};PWD={self.config["password"]};'
            self.liveConn = pyodbc.connect(liveDb)
            self.syncMovie.start()
            self.worker.count = 0
            self.workerThread.start()
            self.workerThread.started.connect(partial(self.worker.syncDispenseData, self.localConn, 
                                                    self.liveConn, self.userData['uid'], triggerBy, 
                                                    self.config['oatRxGetAiDatesApiUrl'], 
                                                    self.config['oatRxPharmacyId'], 
                                                    self.config['oatApiToken']))
        except Exception as e:
            self.handleDatabaseConnectionError(e, database)

    def handleDatabaseConnectionError(self, error, database):
        """Handle database connection error"""
        try:
            self.syncMovie.stop()
            self.frameSettingBtns.show()
            self.frameSync.hide()
            print("Error connecting to SQL Server:", error)
            self.showInfoMessage(f"Error connecting to {database} database", "error")
        except Exception as e:
            print(f"Error in handleDatabaseConnectionError: {e}")

    def showInfoMessage(self, message, messageType):
        """Show info message with appropriate styling"""
        try:
            self.infoSettings.setText(message)
            if messageType == "success":
                self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            else:
                self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
            QTimer.singleShot(2000, self.clearInfoMessages)
        except Exception as e:
            print(f"Error in showInfoMessage: {e}")

    def clearInfoMessages(self):
        """Clear info messages"""
        try:
            self.infoSettings.setText("")
            self.infoSettings.setStyleSheet("background:none")
        except Exception as e:
            print(f"Error in clearInfoMessages: {e}")