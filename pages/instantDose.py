# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from functools import partial
import os, re
from datetime import datetime
import serial.tools.list_ports
import serial.tools,time

class InstantDoseWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.localConn = localConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "instantDose.ui")
        uic.loadUi(ui_path, self)

        localCursor = self.localConn.cursor()
        localCursor.execute("SELECT pump_position, medication from din_groups")
        pumpMedicationDict = {row[0]: row[1] for row in localCursor.fetchall()}
        if pumpMedicationDict:
            self.drugNameLeftInstantDose.setText(pumpMedicationDict['Left'])
            self.drugNameRightInstantDose.setText(pumpMedicationDict['Right'])

        self.fields=[(self.txtDoseLeft,self.errDoseLeft,"Quantity can't be blank"),
                     (self.txtDoseRight,self.errDoseRight,"Quantity can't be blank"),
                    ]
        
        for field,errLabel,errMsg in self.fields:
            self.setState(field, "ok")
            errLabel.setText("")

        self.btnFillLeft.clicked.connect(partial(self.fillInstantDose,triggerBy="LeftPumpBtn"))
        self.txtDoseLeft.returnPressed.connect(partial(self.fillInstantDose,triggerBy="LeftPumpBtn"))
        self.btnFillRight.clicked.connect(partial(self.fillInstantDose,triggerBy="RightPumpBtn"))
        self.txtDoseRight.returnPressed.connect(partial(self.fillInstantDose,triggerBy="RightPumpBtn"))

        self.worker = Worker()
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)
    
    def setState(self,widget, state):
        widget.setProperty("ok2", state == "ok")
        widget.setProperty("error2", state == "err")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def responseInstantFill(self,status,msg):
        try:
            if status == 'error':
                print("Error: ",msg)
                if "could not open port" in msg:
                    self.infoInstantFill.setText("Machine is disconnected. Please connect the machine")
                else:
                    self.infoInstantFill.setText("Something went wrong. Please try again later.")
                self.infoInstantFill.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:9px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
            else:
                self.infoInstantFill.setText("Filling Done")
                self.infoInstantFill.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            QTimer.singleShot(4000, self.clear_info_messages)
            self.progressBarLeft.setRange(0, 100)  # Reset progress bar
            self.progressBarRight.setRange(0, 100)  # Reset progress bar
            self.workerThread.quit()
            self.workerThread.wait()
            self.workerThread.disconnect()
            print("Response Done")
        except Exception as e:
            print(e)

    def fillInstantDose(self,triggerBy=None):
        try:
            for field,errLabel,errMsg in self.fields:
                self.setState(field, "ok")
                errLabel.setText("")

            if triggerBy == 'LeftPumpBtn':
                dose=self.txtDoseLeft.text()

                if str(dose).strip() =="":
                    self.errDoseLeft.setText("Quantity can't be blank ")
                    self.setState(self.txtDoseLeft, "err")
                    return
                
                try:
                    dose=int(self.txtDoseLeft.text())
                except ValueError:
                    try:
                        dose=float(self.txtDoseLeft.text())
                        pattern = r'^-?\d+(\.\d{1,2})?$'
                        if not re.match(pattern, self.txtDoseLeft.text()):
                            self.errDoseLeft.setText("Only 2 digit after decimal are allowed")
                            self.setState(self.txtDoseLeft, "err")
                            return
                    except ValueError:
                        self.errDoseLeft.setText("Only numbers are allowed in quantity")
                        self.setState(self.txtDoseLeft, "err")
                        return
            else:
                dose=self.txtDoseRight.text()
                if str(dose).strip() =="":
                    self.errDoseRight.setText("Quantity can't be blank ")
                    self.setState(self.txtDoseRight, "err")
                    return
                
                try:
                    dose=int(self.txtDoseRight.text())
                except ValueError:
                    try:
                        dose=float(self.txtDoseRight.text())
                        pattern = r'^-?\d+(\.\d{1,2})?$'
                        if not re.match(pattern, self.txtDoseRight.text()):
                            self.errDoseRight.setText("Only 2 digit after decimal are allowed")
                            self.setState(self.txtDoseRight, "err")
                            return
                    except ValueError:
                        self.errDoseRight.setText("Only numbers are allowed in quantity")
                        self.setState(self.txtDoseRight, "err")
                        return

            localCursor = self.localConn.cursor()
            if triggerBy == 'LeftPumpBtn':
                localCursor.execute(f"SELECT id from din_groups where pump_position='Left';")
                command=f"dispense_pump_a {dose}ml"
                progressBar=self.progressBarLeft
            else:
                localCursor.execute(f"SELECT id from din_groups where pump_position='Right';")
                command=f"dispense_pump_b {dose}ml"
                progressBar=self.progressBarRight
            medicationID = localCursor.fetchone()[0]
            localCursor.execute("SELECT lotNo, quantityRemaining FROM stock WHERE dinGroupID=? AND createdAt=(SELECT MAX(createdAt) FROM stock WHERE dinGroupID=?)", (medicationID,medicationID))
            lotDetails=localCursor.fetchone()
            if lotDetails:
                lotDetails={'lotNo':lotDetails[0],'quantityRemaining':lotDetails[1]}
                if lotDetails['quantityRemaining']<dose:
                    if triggerBy == 'LeftPumpBtn':
                        self.errDoseLeft.setText(f"Unable to dispense. Only {lotDetails['quantityRemaining']}ml left")
                        self.setState(self.txtDoseLeft, "err")
                    else:
                        self.errDoseRight.setText(f"Unable to dispense. Only {lotDetails['quantityRemaining']}ml left")
                        self.setState(self.txtDoseRight, "err")
                    return
            
            progressBar.setRange(0, 0)
            self.worker.count=0
            self.workerThread.start()
            self.workerThread.started.connect(partial(self.worker.fillInstantDoseWorker,self.localConn,command,dose,medicationID,lotDetails,self.userData['uid']))
        except Exception as e:
            print(e)

class Worker(QThread):
    instantFill=pyqtSignal(str,str)
    def __init__(self):
        super().__init__()
        self.count = 0
        from otherFiles.config import pcbComPort
        self.pcbComPort = pcbComPort
    def sendPcbCommand(self,command):
        try:
            print(command)
            baudrate=115200
            command += '\n'
            ser = serial.Serial(self.pcbComPort,baudrate, timeout=4)
            ser.write(command.encode())
            time.sleep(0.1)
            # lastMsg=""
            count=1
            while True:
                response = ser.readline().decode()
                print(f"send_pcb_command response {count} -- ",response)
                if "pump - single" in response:
                    pumpType="Single"
                    print("Single pump connected")
                if response in ("Press Y for yes and N for no then press Enter\r\n", "put quantity for calibration in ml\r\n","enter Y for yes and N for no\r\n","Machine is Ready to despense\r\n","wrong input. pls put clb qunatity in numaric format"):
                    # ser.close()
                    print("Serial port closed end of commands")
                    break
                elif response=="":
                    # ser.close()
                    print("Serial port closed blank response")
                    break
                count+=1
            return "Success"
        except Exception as e:
            print("send_pcb_command error",e)
            return e

    def fillInstantDoseWorker(self,localConn,command,dose,medicationID,lotDetails,loginUser):
        try:
            print(" -- instant Fill Dose Worker --")
            self.count+=1
            if self.count>1:
                return
            machineResponse=self.sendPcbCommand(command)
            if machineResponse == "Success":
                local_cursor = localConn.cursor()
                if lotDetails:
                    lotNo=lotDetails['lotNo']
                    totRemaining=lotDetails['quantityRemaining']
                    remaining=totRemaining-dose
                    query = "UPDATE stock SET quantityRemaining=?, updatedBy=?, updatedAt=? WHERE dinGroupID=? AND lotNo=?"
                    values=(remaining,loginUser,datetime.now(),medicationID,lotNo)
                    local_cursor.execute(query,values)
                else:
                    lotNo=None
                query = "INSERT INTO instantDoseLogs (idlMedicationID,idlDose,idlLotNo,createdBy,updatedBy, createdDate, updatedDate) VALUES (?,?,?,?,?,?,?)"
                values=(medicationID,dose,lotNo,loginUser,loginUser,datetime.now(),datetime.now())
                local_cursor.execute(query,values)

                localConn.commit()
                self.instantFill.emit('success','ok')
            else:
                self.instantFill.emit('error',str(machineResponse))
        except Exception as e:
            print(e)
            self.instantFill.emit('error',str(e))