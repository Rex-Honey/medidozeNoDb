# pages/dashboard.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os
import serial.tools.list_ports
from otherFiles.common import sendPcbCommand
from datetime import datetime, timedelta
from PyQt6 import QtCharts
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QMargins, QPointF
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtCharts import QChartView
from PyQt6.QtWidgets import QLabel, QTableWidgetItem
from otherFiles.common import dictfetchall


STYLE_READY = (
    "background:#7FBA00;"
    "font-size:9pt;"
    "padding:6px 8px;"
    "color:#FFFFFF;"
    "border-radius:2%;"
    "font-weight:700;"
)

STYLE_NOT_READY = (
    "padding:6px 8px;"
    "background:#F25022;"
    "font-size:9pt;"
    "color:#FFFFFF;"
    "border-radius:2%;"
    "font-weight:600;"
)

class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import localConn, updatePcbComPort, leftPumpCalibrated, rightPumpCalibrated
        self.localConn = localConn
        self.updatePcbComPort = updatePcbComPort
        self.leftPumpCalibrated = leftPumpCalibrated
        self.rightPumpCalibrated = rightPumpCalibrated
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "dashboard.ui")

        self.worker = Worker()
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)
        self.worker.chkPumpStatus.connect(self.updatePumpStatus)

        uic.loadUi(ui_path, self)
        self.loadInitialData()

    def loadInitialData(self):
        try:
            self.listUsbPorts()
            self.workerThread.start()
            self.workerThread.started.connect(self.worker.checkPumpStatusWorker)
            self.getDispenseDoseAmount()
            self.addDataToTotalDispenseSection()
            self.addDataToTotalPatientSection()
            self.sortDashboardData(0)
        except Exception as e:
            print("load_Initial_Data error:",e)

    def addDataToDashboard(self, dispenseData,triggerBy=None):
        try:
            data_len=len(dispenseData)
            if dispenseData:
                self.lbl_err_data.hide()
                self.frame_11.show()
                self.frame_12.show()
                self.dispenseFrame.show()
                self.patientFrame.show()
                self.tableViewDashboard.show()
                self.tableViewDashboard.setRowCount(data_len)

                for row,row_data in enumerate(dispenseData):
                    col=0
                    rxID=QTableWidgetItem(" "+str(row_data['rxID']))
                    self.tableViewDashboard.setItem(row,col,rxID)
                    self.tableViewDashboard.setColumnWidth(col, 60)

                    col+=1
                    route=QTableWidgetItem(row_data['route'])
                    self.tableViewDashboard.setItem(row,col,route)
                    self.tableViewDashboard.setColumnWidth(col, 30)
                    
                    col+=1
                    patient_name=QTableWidgetItem(row_data['lastName']+", "+row_data['firstName'])
                    self.tableViewDashboard.setItem(row,col,patient_name)
                    self.tableViewDashboard.setColumnWidth(col, 190)
                    
                    col+=1
                    phn=QTableWidgetItem(str(row_data['patientID']))
                    self.tableViewDashboard.setItem(row,col,phn)
                    self.tableViewDashboard.setColumnWidth(col, 100)

                    col+=1
                    phone=QTableWidgetItem(str(row_data['areaCode'])+str(row_data['phone']))
                    self.tableViewDashboard.setItem(row,col,phone)
                    self.tableViewDashboard.setColumnWidth(col, 120)

                    col+=1
                    drug=QTableWidgetItem(row_data['rxDrug'])
                    self.tableViewDashboard.setItem(row,col,drug)
                    self.tableViewDashboard.setColumnWidth(col, 210)

                    col+=1
                    totProcessing=row_data['totProcessing']
                    if totProcessing==int(totProcessing):
                        totProcessing=int(totProcessing)
                    dose=QTableWidgetItem(str(totProcessing)+"ml")
                    self.tableViewDashboard.setColumnWidth(col, 40)
                    self.tableViewDashboard.setItem(row,col,dose)
            else:
                self.tableViewDashboard.hide()
                if triggerBy=="sortDashboard":
                    self.frame_12.hide()
                    self.frame_11.hide()
                    self.dispenseFrame.hide()
                    self.patientFrame.hide()
        except Exception as e:
            print(e)

    def sortDashboardData(self,index):
        try:
            # currentDate = datetime(2024, 11, 20)
            currentDate=datetime.now()
            formattedCurrentDate = currentDate.strftime('%Y-%m-%d %H:%M:%S')
            self.headingDashboard.setText("Dispense for the day " +currentDate.strftime("%b %d, %y"))

            localCursor = self.localConn.cursor()
            if index==0:
                localCursor.execute(f"SELECT rx.rxID, rx.rxDin, patient.route, patient.firstName, patient.lastName, refill.patientID, patient.areaCode, patient.phone, refill.totProcessing, rx.rxDrug from refill JOIN patient ON patient.id = refill.patientID LEFT JOIN rx on rx.rxID=refill.rxID WHERE CONVERT(date,refill.reefDate)='{formattedCurrentDate}' order by patient.lastName")
            elif index==1:
                localCursor.execute(f"SELECT rx.rxID, rx.rxDin, patient.route, patient.firstName, patient.lastName, refill.patientID, patient.areaCode, patient.phone, refill.totProcessing, rx.rxDrug from refill JOIN patient ON patient.id = refill.patientID LEFT JOIN rx on rx.rxID=refill.rxID WHERE CONVERT(date,refill.reefDate)='{formattedCurrentDate}' order by route")
            dispenseData=dictfetchall(localCursor)

            filtered_data = {}
            for row in dispenseData:
                patient_id = row['patientID']
                if patient_id not in filtered_data:
                    filtered_data[patient_id] = row
                else:
                    if row['rxID'] > filtered_data[patient_id]['rxID']:
                        filtered_data[patient_id] = row
            dispenseData = list(filtered_data.values())  # Convert back to a list

            self.addDataToDashboard(dispenseData,triggerBy="sortDashboard")
        except Exception as e:
            print(e)

    def listUsbPorts(self):
        try:
            print("\nlist Usb Ports")
            ports = serial.tools.list_ports.comports()
            portsDetails=[]
            pcbConnected=False
            for port in ports:
                portData={}
                portData["name"] = port.name
                portData["device"] = port.device
                portData["description"] = port.description
                portData["hwid"] = port.hwid
                portData["interface"] = port.interface
                portData["location"] = port.location
                portData["manufacturer"] = port.manufacturer
                portData["pid"] = port.pid
                portData["product"] = port.product
                portData["serial_number"] = port.serial_number
                portData["vid"] = port.vid
                portsDetails.append(portData)
                if 'USB-SERIAL CH340' in port.description:
                    self.updatePcbComPort(portData)
                    pcbConnected=True
                    self.worker.pcbComPort = portData["device"]
            if not pcbConnected:
                print("PCB not connected")
        except Exception as e:
            print("list_Usb_Ports error:",e)

    def updatePumpStatus(self,status):
        try:
            if status == 'ok':
                if self.leftPumpCalibrated:
                    self.btnStatusPumpLeft.setText("READY")
                    self.btnStatusPumpLeft.setStyleSheet(STYLE_READY)
                    self.btnStatusPumpLeft.setCursor(Qt.CursorShape.ArrowCursor)
                    print("Left Pump ready")
                else:
                    self.btnStatusPumpLeft.setText("Uncalibrated")
                    self.btnStatusPumpLeft.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.btnStatusPumpLeft.setStyleSheet(STYLE_NOT_READY)
                    print("Left Pump uncalibrated")
                if self.rightPumpCalibrated:
                    self.btnStatusPumpRight.setText("READY")
                    self.btnStatusPumpRight.setStyleSheet(STYLE_READY)
                    self.btnStatusPumpRight.setCursor(Qt.CursorShape.ArrowCursor)
                    print("Right Pump ready")
                else:
                    self.btnStatusPumpRight.setText("Uncalibrated")
                    self.btnStatusPumpRight.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.btnStatusPumpRight.setStyleSheet(STYLE_NOT_READY)
                    print("Right Pump uncalibrated")
            else:
                self.btnStatusPumpLeft.setText("Offline")
                self.btnStatusPumpLeft.setStyleSheet(STYLE_NOT_READY)
                self.btnStatusPumpLeft.setCursor(Qt.CursorShape.ArrowCursor)
                self.btnStatusPumpRight.setText("Offline")
                self.btnStatusPumpRight.setStyleSheet(STYLE_NOT_READY)
                self.btnStatusPumpRight.setCursor(Qt.CursorShape.ArrowCursor)
            self.workerThread.quit()
            self.workerThread.wait()
            try:
                self.workerThread.started.disconnect()
            except (TypeError, RuntimeError):
                pass
        except Exception as e:
            print("update_Pump_Status error:",e)

    def getDispenseDoseAmount(self):
        try:
            currentDate=datetime.now()
            formattedCurrentDate = currentDate.strftime('%Y-%m-%d %H:%M:%S')
            localCursor = self.localConn.cursor()
            localCursor.execute(f"""SELECT 
                COALESCE(ROUND(( 
                    SELECT SUM(dl.dlDose) 
                    FROM dispenseLogs dl 
                    JOIN din_groups dg ON dg.id = dl.dlMedicationID 
                    WHERE dg.pump_position = 'Left' 
                    AND CONVERT(date,dl.createdDate) = '{formattedCurrentDate}'
                ), 2), 0) + 
                COALESCE(ROUND(( 
                    SELECT SUM(idl.idlDose) 
                    FROM instantDoseLogs idl 
                    JOIN din_groups dg ON dg.id = idl.idlMedicationID 
                    WHERE dg.pump_position = 'Left' 
                    AND CONVERT(date,idl.createdDate) = '{formattedCurrentDate}'
                ), 2), 0) AS total_left_pump, 
                COALESCE(ROUND(( 
                    SELECT SUM(dl.dlDose) 
                    FROM dispenseLogs dl 
                    JOIN din_groups dg ON dg.id = dl.dlMedicationID 
                    WHERE dg.pump_position = 'Right' 
                    AND CONVERT(date,dl.createdDate) = '{formattedCurrentDate}'
                ), 2), 0) + 
                COALESCE(ROUND(( 
                    SELECT SUM(idl.idlDose) 
                    FROM instantDoseLogs idl 
                    JOIN din_groups dg ON dg.id = idl.idlMedicationID 
                    WHERE dg.pump_position = 'Right' 
                    AND CONVERT(date,idl.createdDate) = '{formattedCurrentDate}'
                ), 2), 0) AS total_right_pump""")
            dispenseTotal = localCursor.fetchall()[0]
            totalLeft=dispenseTotal[0]
            totalRight=dispenseTotal[1]
            if totalLeft==int(totalLeft):
                totalLeft=int(totalLeft)
            self.lblFilledLeft.setText(str(totalLeft))
            if totalRight==int(totalRight):
                totalRight=int(totalRight)
            self.lblFilledRight.setText(str(totalRight))
        except Exception as e:
            print("get_Dispense_Dose_Amount error:",e)

    def addDataToTotalDispenseSection(self):
        try:
            layout = self.dispenseFrame.layout()
            for _ in range(layout.count()):
                item = layout.takeAt(0)
                if item:
                    widget = item.widget().deleteLater()

            # date_obj = datetime(2024, 7, 2)
            date_obj=datetime.now()
            day=date_obj-timedelta(days=4)
            daysNames=[]
            localCursor = self.localConn.cursor()
            stringDates=[]
            # dataList=[]
            for _ in range(5):
                daysNames.append(day.strftime('%A')[:3])
                stringDates.append(day.strftime('%Y-%m-%d'))
                day+=timedelta(days=1)
            localCursor.execute(
                f"""
                SELECT 
                    date, 
                    SUM(TotalDose) AS TotalDose 
                FROM 
                    (
                    SELECT 
                        CONVERT(date, dispenseLogs.createdDate) AS date, 
                        COALESCE(ROUND(SUM(dlDose), 2), 0) AS TotalDose 
                    FROM 
                        dispenseLogs 
                    WHERE 
                        CONVERT(date, dispenseLogs.createdDate) IN {tuple(stringDates)}
                    GROUP BY 
                        createdDate
                    UNION ALL
                    SELECT 
                        CONVERT(date, instantDoseLogs.createdDate) AS date, 
                        COALESCE(ROUND(SUM(idlDose), 2), 0) AS TotalDose 
                    FROM 
                        instantDoseLogs 
                    WHERE 
                        CONVERT(date, instantDoseLogs.createdDate) IN {tuple(stringDates)} 
                    GROUP BY 
                        createdDate
                    ) AS combined
                GROUP BY 
                    date
                """
            )
            queryFiveDaysDict = {row[0]:row[1] for row in localCursor.fetchall()}
            fiveDaysData=[]
            for stringDate in stringDates:
                value=queryFiveDaysDict.get(stringDate,0)
                if value==int(value):
                    value=int(value)
                else:
                    value=round(value,1)
                if stringDate in queryFiveDaysDict:
                    fiveDaysData.append(value)
                else:
                    fiveDaysData.append(0)


            series=QtCharts.QBarSeries()
            # values=[30,40,50,60,70]

            bar1=QtCharts.QBarSet("bar1") # name if multiple bars

            for yval in fiveDaysData:
                bar1.append(yval)
                
            series.append(bar1)

            chart=QtCharts.QChart()
            chart.setMargins(QMargins(0, 10, 0, 0))
            chart.legend().setVisible(False)
            chart.addSeries(series)
            chart.setAnimationOptions(QtCharts.QChart.AnimationOption.AllAnimations)

            axisX=QtCharts.QBarCategoryAxis()
            font=axisX.labelsFont()
            font.setPixelSize(10)
            axisX.setLabelsFont(font)
            axisX.append(daysNames)
            # axisX.setTitleText('Days')
            axisX.setGridLineVisible(False)
            chart.addAxis(axisX,Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axisX)

            axisY=QtCharts.QValueAxis()
            font=axisY.labelsFont()
            font.setPixelSize(10)
            axisY.setLabelsFont(font)
            axisY.setLabelFormat('%d')
            if all(value < 3 for value in fiveDaysData):
                axisY.setRange(0, 3)
            axisY.setTickCount(4)
            chart.addAxis(axisY,Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axisY)
            
            self.dispenseGraph = CustomChartView(chart, fiveDaysData)
            self.dispenseGraph.setMinimumHeight(200)
            self.dispenseGraph.setRenderHint(QPainter.RenderHint.Antialiasing)
            label = QLabel("Last 5 days dispense")
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            label.setStyleSheet("font-size: 14px; font-weight: bold;margin-top:10px")
            layout.addWidget(label)
            layout.addWidget(self.dispenseGraph)
        except Exception as e:
            print(e)

    def addDataToTotalPatientSection(self):
        try:
            layout = self.patientFrame.layout()
            for _ in range(layout.count()):
                item = layout.takeAt(0)
                if item:
                    widget = item.widget().deleteLater()

            date_obj=datetime.now()
            # date_obj = datetime(2024, 7, 2)
            day=date_obj-timedelta(days=4)
            daysNames=[]
            stringDates=[]
            for _ in range(5):
                daysNames.append(day.strftime('%A')[:3])
                stringDates.append(day.strftime('%Y-%m-%d'))
                day+=timedelta(days=1)

            localCursor = self.localConn.cursor()
            localCursor.execute(f"SELECT CONVERT(date,dispenseLogs.createdDate) as date, COUNT(DISTINCT [dlpatientID]) as patientId from dispenseLogs WHERE CONVERT(date,dispenseLogs.createdDate) in {tuple(stringDates)} GROUP BY CONVERT(date,dispenseLogs.createdDate)")
            queryFiveDaysData=localCursor.fetchall()
            queryFiveDaysDict = {row[0]:row[1] for row in queryFiveDaysData}
            fiveDaysData = [queryFiveDaysDict[stringDate] if stringDate in queryFiveDaysDict else 0 for stringDate in stringDates]


            series=QtCharts.QBarSeries()
            bar1=QtCharts.QBarSet("bar1")

            for yval in fiveDaysData:
                bar1.append(yval)
                
            series.append(bar1)

            chart=QtCharts.QChart()
            chart.setMargins(QMargins(0, 10, 0, 0))
            chart.legend().setVisible(False)
            chart.addSeries(series)
            chart.setAnimationOptions(QtCharts.QChart.AnimationOption.AllAnimations)

            axisX=QtCharts.QBarCategoryAxis()
            font=axisX.labelsFont()
            font.setPixelSize(10)
            axisX.setLabelsFont(font)
            axisX.append(daysNames)
            axisX.setGridLineVisible(False)
            chart.addAxis(axisX,Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axisX)

            axisY=QtCharts.QValueAxis()
            font=axisY.labelsFont()
            font.setPixelSize(10)
            axisY.setLabelsFont(font)
            axisY.setLabelFormat('%d')
            if all(value < 3 for value in fiveDaysData):
                axisY.setRange(0, 3)
            axisY.setTickCount(4)
            chart.addAxis(axisY,Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axisY)

            # ========= old method =================
            # self.patientGraph = QtCharts.QChartView()
            # self.patientFrame.layout().addWidget(self.patientGraph)
            # chart.setTitle("Last 5 days Patients")
            # self.patientGraph.setChart(chart)

            self.patientGraph = CustomChartView(chart, fiveDaysData)
            self.patientGraph.setMinimumHeight(200)
            self.patientGraph.setRenderHint(QPainter.RenderHint.Antialiasing)
            label = QLabel("Last 5 days Patients")
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            label.setStyleSheet("font-size: 14px; font-weight: bold;margin-top:10px")
            layout.addWidget(label)
            self.patientFrame.layout().addWidget(self.patientGraph)
        except Exception as e:
            print(e)

class CustomChartView(QChartView):
    def __init__(self, chart, values):
        super().__init__(chart)
        self.values = values

    def drawLabels(self, painter):
        chart = self.chart()
        series = chart.series()[0]
        barset = series.barSets()[0]
        rect = chart.plotArea()
        bar_width = rect.width() / len(self.values)
        for i, value in enumerate(self.values):
            # Calculate bar center
            x = rect.left() + bar_width * (i + 0.5)
            y = chart.mapToPosition(QPointF(i, value), series).y()
            # label = f"{value:.1f}"
            label = f"{value}"
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            if value>0:
                painter.drawText(int(x)-10, int(y)-5, label)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        self.drawLabels(painter)
        painter.end()

class Worker(QObject):
    chkPumpStatus=pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.pcbComPort = None

    def checkPumpStatusWorker(self):
        try:
            machineResponse = sendPcbCommand(self.pcbComPort, 'check_status')
            if machineResponse == "Success":
                self.chkPumpStatus.emit('ok')
            else:
                self.chkPumpStatus.emit('error')
        except Exception as e:
            print("check_Pump_Status_Worker error:",e)
            self.chkPumpStatus.emit('error')
