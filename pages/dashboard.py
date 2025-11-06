# pages/dashboard.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc
import serial.tools.list_ports
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from otherFiles.common import sendPcbCommand
from datetime import datetime

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
            self.getDispenseDoseAmount()
            self.listUsbPorts()
            self.workerThread.start()
            self.workerThread.started.connect(self.worker.checkPumpStatusWorker)
        except Exception as e:
            print("load_Initial_Data error:",e)

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