# pages/dashboard.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc
import serial.tools.list_ports
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
import time


class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn, leftPumpMedication, rightPumpMedication, updatePcbComPort
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.localConn = localConn
        self.updatePcbComPort = updatePcbComPort
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "dashboard.ui")

        self.worker = Worker()
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)

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
            self.workerThread.start()
            self.workerThread.started.connect(self.worker.checkPumpStatusWorker)
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

class Worker(QObject):
    chkPumpStatus=pyqtSignal(str)
    def __init__(self):
        super().__init__()
        from otherFiles.config import pcbComPort
        self.pcbComPort = pcbComPort

    def checkPumpStatusWorker(self):
        try:
            machineResponse=self.sendPcbCommand('check_status')
            if machineResponse == "Success":
                self.chkPumpStatus.emit('ok')
            else:
                self.chkPumpStatus.emit('error')
        except Exception as e:
            print("check_Pump_Status_Worker error",e)
            self.chkPumpStatus.emit('error')

    def sendPcbCommand(self,command):
        try:
            print(command)
            baudrate=115200
            payload = f"{command.strip()}\n".encode("utf-8")
            with serial.Serial(
                self.pcbComPort,
                baudrate,
                timeout=1.0,
                write_timeout=2.0,
            ) as ser:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.write(payload)
                ser.flush()
                time.sleep(0.05)

                responses = []
                empty_reads = 0
                max_empty_reads = 3
                max_duration = 8.0
                start_time = time.monotonic()

                while time.monotonic() - start_time < max_duration:
                    raw_response = ser.readline()
                    if not raw_response:
                        empty_reads += 1
                        if empty_reads >= max_empty_reads:
                            print("send_pcb_command: reached empty read limit")
                            break
                        continue

                    empty_reads = 0
                    response = raw_response.decode("utf-8", errors="ignore").strip()
                    if not response:
                        continue

                    responses.append(response)
                    print(f"send_pcb_command response {len(responses)} -- {response}")

                    response_lower = response.lower()
                    if "pump - single" in response_lower:
                        print("Single pump connected")

            return "Success"
        except Exception as e:
            print("send_pcb_command error",e)
            return e