# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QDateTime, QTime
from PyQt6 import uic
from .lotDialog import LotDialog
from functools import partial
from datetime import datetime
from otherFiles.common import dictfetchall
import os, pyodbc

class DispenseWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn, liveConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.local_conn = localConn
        self.liveConn = liveConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "dispense.ui")
        uic.loadUi(ui_path, self)

        self.lotDialog=LotDialog()
        self.lotDialog.show()
        self.fetchDispenseData(triggerBy="switchDispense")

    def fetchDispenseData(self, triggerBy=None):
        try:
            if triggerBy == "switchDispense":
                self.dateEditViewDispense.dateChanged.disconnect()
                self.dateEditViewDispense.setDate(datetime.now())
                self.dateEditViewDispense.dateChanged.connect(partial(self.fetchDispenseData, triggerBy="DateEdit"))
                formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                selected_date = QDateTime(self.dateEditViewDispense.date(), QTime(0, 0))
                formatted_date = selected_date.toString('yyyy-MM-dd hh:mm:ss')
            findPatient = str(self.txtSearchPatientDispense.text()).strip()
            sortIndex = self.sortDispenseCombo.currentIndex()
            drugIndex = self.comboDrug.currentIndex()
            drugText = self.comboDrug.currentText()
            routeIndex = self.comboRoute.currentIndex()
            routeText = self.comboRoute.currentText()
            local_cursor = self.local_conn.cursor()

            baseQuery = f"""SELECT patient.route, patient.firstName, patient.lastName, patient.gender, refill.patientID, patient.areaCode, patient.phone, rx.rxID, rx.rxDrug, rx.rxOrigDate, rx.rxStopDate, rxQty, rx.rxType, rx.rxDrFirst, rx.rxDrLast, rx.rxSig, rx.rxDin, rx.rxDays, rx.scDays, rx.scheduleType, rx.isChanging, rx.carryEnabled, refill.reefDate, refill.prevDate, refill.witness, refill.carry, refill.frequency, refill.emergencyCount, refill.totRemaining, refill.totProcessing, refill.emergencyCount, refill.reJudge, refill.reReason from refill JOIN patient ON patient.id = refill.patientID LEFT JOIN rx on rx.rxID=refill.rxID WHERE CONVERT(date,refill.reefDate)='{formatted_date}' AND rx.rxStat not in ('N','S','Tsf')"""
            conditions = []

            if triggerBy in ("switchDispense",'DateEdit'):
                query = baseQuery
            else:
                if drugIndex > 1:
                    conditions.append(f" AND rx.rxDrug='{drugText}'")

                if routeIndex > 1:
                    conditions.append(f" AND patient.route='{routeText}'")

                if findPatient:
                    if "," in findPatient:
                        findPatient = findPatient.split(",")
                        firstName = str(findPatient[1]).strip()
                        lastName = str(findPatient[0]).strip()
                        conditions.append(
                            f" AND patient.firstName LIKE '%{firstName}%' AND patient.lastName LIKE '%{lastName}%'")
                    else:
                        conditions.append(
                            f" AND (patient.firstName LIKE '%{findPatient}%' OR patient.lastName LIKE '%{findPatient}%' OR patient.id LIKE '%{findPatient}%' OR patient.phone LIKE '%{findPatient}%' OR rx.rxID LIKE '%{findPatient}%')")

                if conditions:
                    query = baseQuery + "".join(conditions)  # Combine conditions with baseQuery
                else:
                    query = baseQuery

            if sortIndex == 0:
                query += " order by patient.lastName"
            else:
                query += " order by route"

            local_cursor.execute(query)
            data = dictfetchall(local_cursor)
            print("fetched dispense data")
            finalData=[]
            if data:
                # Get Stoped rx data from live db
                rxList = [row['rxID'] for row in data]
                placeholders = ','.join(['?'] * len(rxList))
                liveCursor=self.liveConn.cursor()
                query=f"select RXNUM,RXSTOP from RX WHERE RXNUM IN ({placeholders})"
                liveCursor.execute(query,rxList)
                liveRxData=dictfetchall(liveCursor)
                self.stopedRx=[]
                if liveRxData:
                    for rx in liveRxData:
                        if rx['RXSTOP'] and rx['RXSTOP'].date()<datetime.now().date():
                            self.stopedRx.append(rx['RXNUM'])

                # Remove duplicate patientIDs and stopeed rx, keeping the record with the highest rxID
                filtered_data = {}
                for row in data:
                    patient_id = row['patientID']
                    if row['rxID'] not in self.stopedRx:
                        if patient_id not in filtered_data:
                            filtered_data[patient_id] = row
                        else:
                            if row['rxID'] > filtered_data[patient_id]['rxID']:
                                filtered_data[patient_id] = row

                finalData = list(filtered_data.values())  # Convert back to a list

            if triggerBy in ("switchDispense",'DateEdit'):
                drugs = list({item["rxDrug"] for item in finalData})
                drugs.sort()
                for i in range(self.comboDrug.count()):
                    if i>1:
                        self.comboDrug.removeItem(2)
                for drug in drugs:
                    self.comboDrug.addItem(drug)

                routes = list({item["route"] for item in finalData})
                routes.sort()
                for i in range(self.comboRoute.count()):
                     if i>1:
                        self.comboRoute.removeItem(2)
                for route in routes:
                    self.comboRoute.addItem(route)
                    
                if triggerBy == "DateEdit":
                    self.comboDrug.setCurrentText(drugText)
                    self.comboRoute.setCurrentText(routeText)

            if not finalData:
                self.tableDispense.hide()
                self.lblDB.show()
                return

            self.tableDispense.show()
            self.lblDB.hide()
            self.addDataToDispense(finalData)

            for i in range(12, self.tableDispense.columnCount()):
                self.tableDispense.setColumnHidden(i, True)

            if triggerBy == "DateEdit":
                self.fetchDispenseData()

        except Exception as e:
            print(f"Error in fetch Dispense Data: {e}")

    def addDataToDispense(self, data):
        try:
            data_len=len(data)
            self.tableDispense.setRowCount(data_len)
            self.infoViewDispense.hide()
            if self.labelType=="normal":
                printFunction=self.generateNormalLabel
            else:
                printFunction=self.generateInvertedLabel
            if data:
                print()
                for row,row_data in enumerate(data):
                    print("adding rx to table",row_data['rxID'])
                    # if row_data['rxID']==28052:
                    #     print("stop")
                    if row_data['reReason']:
                        continue
                    if row_data['isChanging']=='Y':
                        ChangingDoseColor = QColor("blue")
                    else:
                        ChangingDoseColor = QColor("black")
                    col=0
                    rxID=QTableWidgetItem(" "+str(row_data['rxID']))
                    if row_data['emergencyCount']>0:
                        rxID.setForeground(QBrush(QColor("red")))
                    self.tableDispense.setItem(row,col,rxID)
                    self.tableDispense.setColumnWidth(col, 60)

                    col=1
                    route=QTableWidgetItem(row_data['route'])
                    self.tableDispense.setItem(row,col,route)
                    self.tableDispense.setColumnWidth(col, 40)

                    col+=1
                    patient_name=QTableWidgetItem(row_data['lastName']+" "+row_data['firstName'])
                    self.tableDispense.setItem(row,col,patient_name)
                    self.tableDispense.setColumnWidth(col, 180)

                    col+=1
                    phn=QTableWidgetItem(str(row_data['patientID']))
                    phn.setForeground(QBrush(ChangingDoseColor))
                    self.tableDispense.setItem(row,col,phn)
                    self.tableDispense.setColumnWidth(col, 90)

                    col+=1
                    phone=QTableWidgetItem(str(row_data['areaCode'])+str(row_data['phone']))
                    self.tableDispense.setItem(row,col,phone)
                    self.tableDispense.setColumnWidth(col, 90)

                    col+=1
                    drug=QTableWidgetItem(row_data['rxDrug'])
                    self.tableDispense.setItem(row,col,drug)
                    self.tableDispense.setColumnWidth(col, 210)

                    col+=1
                    witness=row_data['witness']
                    if witness==int(witness):
                        witness=int(witness)
                    else:
                        witness=round(witness,1)
                    witnessLbl=QTableWidgetItem(str(witness)+"ml")
                    self.tableDispense.setItem(row,col,witnessLbl)
                    self.tableDispense.setColumnWidth(col, 60)

                    col+=1
                    carryStr=row_data['carry']
                    if "," in carryStr:
                        carryArr=carryStr.split(",")
                        carry=0
                        for i in carryArr:
                            carryVal=float(i)
                            if carryVal==int(carryVal):
                                carryVal=int(carryVal)
                            carry=carry+carryVal
                    else:
                        carry=float(carryStr)
                    if carry==int(carry):
                        carry=int(carry)
                    else:
                        carry=round(carry,1)
                    if carry:
                        carryLbl=QTableWidgetItem(str(carry)+"ml")
                    else:
                        carryLbl=QTableWidgetItem(str(carry))
                    self.tableDispense.setItem(row,col,carryLbl)
                    self.tableDispense.setColumnWidth(col, 50)
                    
                    col+=1
                    frequency=QTableWidgetItem(row_data['frequency'])
                    self.tableDispense.setItem(row,col,frequency)
                    self.tableDispense.setColumnWidth(col, 40)

                    if row_data['frequency'] !="OD":
                        totalCarry=carryStr.split(",")
                        copies=len(totalCarry)+1
                    else:
                        copies=int(carry/witness)+1

                    col+=1
                    btnPrint = QPushButton()
                    btnPrint.setIcon(QIcon(self.iconPrint))
                    btnPrint.setStyleSheet("background-color:transparent;")
                    btnPrint.setCursor(Qt.CursorShape.PointingHandCursor)
                    btnPrint.clicked.connect(partial(printFunction,row_data,copies))
                    self.tableDispense.setCellWidget(row,col,btnPrint)
                    self.tableDispense.setColumnWidth(col, 50)
                    
                    col+=1
                    allRefillsFilledForDay = True
                    date=row_data['reefDate']
                    totDays=int(carry/witness)+1
                    for _ in range(totDays):
                        reefDate = date.strftime('%Y-%m-%d %H:%M:%S')
                        local_cursor = self.local_conn.cursor()
                        local_cursor.execute(f"SELECT COUNT(*) FROM dispenseLogs WHERE dlRxID={row_data['rxID']} AND CONVERT(date,dlReefDate) = '{reefDate}'")
                        count = local_cursor.fetchone()[0]
                        if count > 0:
                            pass
                        else:
                            allRefillsFilledForDay=False
                            break
                        date+=timedelta(days=1)
                    btnFill = QPushButton("Fill Now")
                    btnFillAndPrint = QPushButton("Fill + Print")
                    btnFill.setStyleSheet("margin:3px;background:#FFFFFF;color:#48C9E3;border:1px solid #48C9E3;border-radius:6%;font-weight:700")
                    btnFill.setCursor(Qt.CursorShape.PointingHandCursor)

                    btnFillAndPrint.setStyleSheet("margin:3px;background:#FFFFFF;color:#48C9E3;border:1px solid #48C9E3;border-radius:6%;font-weight:700")
                    btnFillAndPrint.setCursor(Qt.CursorShape.PointingHandCursor)
                    if allRefillsFilledForDay:
                        btnFill.setText("Refill")
                        btnFill.setStyleSheet("margin:3px;background:#48C9E3;color:#FFFFFF;border:1px solid #48C9E3;border-radius:6%;font-weight:700")

                        # btnFill.setStyleSheet("margin:3px;border:1px solid green;color:green;border-radius:6%;")
                        # btnFill.setIcon(QIcon(self.iconCheck))

                        btnFillAndPrint.setStyleSheet("margin:3px;background:#48C9E3;color:#FFFFFF;border:1px solid #48C9E3;border-radius:6%;font-weight:700")
                        # btnFillAndPrint.setStyleSheet("margin:3px;border:1px solid green;color:green;border-radius:6%;")
                        # btnFillAndPrint.setIcon(QIcon(self.iconCheck))
                    btnFill.clicked.connect(partial(self.fillDrugPopup, row_data,btnFill,btnFillAndPrint))
                    btnFillAndPrint.clicked.connect(partial(self.fillAndPrint, row_data,btnFill,btnFillAndPrint,copies))

                    btnFill.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                    self.tableDispense.setCellWidget(row,col,btnFill)
                    self.tableDispense.setColumnWidth(col, 70)
                    
                    col+=1
                    btnFillAndPrint.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                    self.tableDispense.setCellWidget(row,col,btnFillAndPrint)
                    
                    # hidden columns =========================================================
                    col+=1
                    rxType=QTableWidgetItem(row_data['rxType'])
                    self.tableDispense.setItem(row,col,rxType)
                    col+=1
                    rxId=QTableWidgetItem(str(row_data['rxID']))
                    self.tableDispense.setItem(row,col,rxId)
                    col+=1
                    if row_data['rxOrigDate']:
                        formattedOrigDate = row_data['rxOrigDate'].strftime('%Y-%m-%d %H:%M:%S')
                        origDate=QTableWidgetItem(formattedOrigDate)
                        self.tableDispense.setItem(row,col,origDate)
                    else:
                        self.tableDispense.setItem(row,col,QTableWidgetItem(""))
                    col+=1
                    if row_data['rxStopDate']:
                        formattedStopDate = row_data['rxStopDate'].strftime('%Y-%m-%d %H:%M:%S')
                        stopDate=QTableWidgetItem(formattedStopDate)
                        self.tableDispense.setItem(row,col,stopDate)
                    else:
                        self.tableDispense.setItem(row,col,QTableWidgetItem(""))
                    col+=1
                    totDays=QTableWidgetItem(str(row_data['rxDays']))
                    self.tableDispense.setItem(row,col,totDays)
                    col+=1
                    totQty=QTableWidgetItem(str(row_data['rxQty']))
                    self.tableDispense.setItem(row,col,totQty)
                    col+=1
                    rxSig=QTableWidgetItem(row_data['rxSig'])
                    self.tableDispense.setItem(row,col,rxSig)
                    col+=1
                    totRemaining=QTableWidgetItem(str(row_data['totRemaining']))
                    self.tableDispense.setItem(row,col,totRemaining)
                    col+=1
                    prevDate=QTableWidgetItem(str(row_data['prevDate']))
                    self.tableDispense.setItem(row,col,prevDate)
                    col+=1
                    scDays=QTableWidgetItem(str(row_data['scDays']))
                    self.tableDispense.setItem(row,col,scDays)
                    col+=1
                    emergencyCount=QTableWidgetItem(str(row_data['emergencyCount']))
                    self.tableDispense.setItem(row,col,emergencyCount)
                    col+=1
                    gender=QTableWidgetItem(row_data['gender'])
                    self.tableDispense.setItem(row,col,gender)
                    col+=1
                    scheduleType=QTableWidgetItem(row_data['scheduleType'])
                    self.tableDispense.setItem(row,col,scheduleType)
                    col+=1
                    carryEnabled=QTableWidgetItem(row_data['carryEnabled'])
                    self.tableDispense.setItem(row,col,carryEnabled)
                    col+=1
                print("all Rx added")
        except Exception as e:
            print(e)