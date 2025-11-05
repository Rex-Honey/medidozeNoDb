# pages/dashboard.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc
import serial.tools.list_ports

class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn, updatePcbComPort
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.localConn = localConn
        self.updatePcbComPort = updatePcbComPort
        
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "dashboard.ui")

        uic.loadUi(ui_path, self)
        self.loadInitialData()

    def loadInitialData(self):
        try:
            self.listUsbPorts()
            localCursor = self.localConn.cursor()
            localCursor.execute(f"SELECT pump_position, medication FROM din_groups;")
            medications = localCursor.fetchall()
            pumpMedicationDict = {row[0]: row[1] for row in medications}
            if 'Left' in pumpMedicationDict:
                self.medPumpLeft.setText(pumpMedicationDict['Left'])
            if 'Right' in pumpMedicationDict:
                self.medPumpRight.setText(pumpMedicationDict['Right'])
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
            if not pcbConnected:
                print("PCB not connected")
        except Exception as e:
            print(e)
