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
            # self.addDataToDispense(finalData)

            for i in range(12, self.tableDispense.columnCount()):
                self.tableDispense.setColumnHidden(i, True)

            if triggerBy == "DateEdit":
                self.fetchDispenseData()

        except Exception as e:
            print(f"Error in fetch Dispense Data: {e}")