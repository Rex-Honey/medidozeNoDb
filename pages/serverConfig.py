import os,pyodbc,json,threading,time
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QTimer
from datetime import datetime
from hashlib import sha256
from PyQt6.QtCore import QStandardPaths

class ServerConfigWindow(QWidget):
    serverSetUpDone = pyqtSignal(dict,str)
    def __init__(self):
        super().__init__()
        rootDir=os.path.dirname(os.path.dirname(__file__))
        uic.loadUi(os.path.join(rootDir, 'uiFiles', 'serverConfig.ui'), self)
        self.btnConnect.clicked.connect(self.connectServer)
        for wid in (self.txtServerIP,self.txtServerName,self.txtPort,self.txtUsername,self.txtPassword):
            self.setState(wid,"ok")

    def setState(self, widget, state):
        widget.setProperty("server", state == "ok")
        widget.setProperty("serverError", state == "err")
        widget.style().unpolish(widget)
        widget.style().polish(widget)


    def connectServer(self):
        try:
            fields = [
                (self.txtServerIP, self.errServerIP, "Server IP Name can't be blank"),
                (self.txtServerName, self.errServerName, "Server Name can't be blank"),
                (self.txtPort, self.errTcpPort, "Port Number can't be blank"),
                (self.txtUsername, self.errUsername, "Username can't be blank"),
                (self.txtPassword, self.errPassword, "Password can't be blank"),
            ]

            for widget, error_label, error_msg in fields:
                self.setState(widget, "ok")
                error_label.setText("")
                if widget.text().strip() == "":
                    self.setState(widget, "err")
                    error_label.setText(error_msg)
                    return

            serverIP=self.txtServerIP.text()
            serverPort=self.txtPort.text()
            serverName=self.txtServerName.text()
            username=self.txtUsername.text()
            password=self.txtPassword.text()

            # serverIP="192.168.29.151"
            # serverPort="1433"
            # serverName="SQLEXPRESS"
            # username="sa"
            # password="dexter"

            config={
                    "server":f"{serverIP},{serverPort}\\{serverName}",
                    "local_database":"medidoze",
                    "username":f"{username}",
                    "password":f"{password}"
            }
            
            connectionString = (
                "DRIVER={SQL Server};"
                'SERVER='f"{serverIP},{serverPort}\\{serverName};"
                "DATABASE=medidoze;"
                'UID='f"{username};"
                'PWD='f'{password};'
            )

                # Connection result storage
            connection_result = {'success': False, 'connection': None, 'error': None}
            
            def attempt_connection():
                try:
                    conn = pyodbc.connect(connectionString)
                    connection_result['success'] = True
                    connection_result['connection'] = conn
                except Exception as e:
                    connection_result['error'] = e
            
            # Start connection attempt in a separate thread
            conn_thread = threading.Thread(target=attempt_connection)
            conn_thread.daemon = True
            conn_thread.start()
            
            # Wait for 2 seconds maximum
            conn_thread.join(timeout=2)
            
            if connection_result['success']:
                self.local_conn = connection_result['connection']
                self.config=config
                print("Connection successful!")
                documentsDir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
                medidozeDir = os.path.join(documentsDir, 'medidoze')
                os.makedirs(medidozeDir, exist_ok=True)
                with open(os.path.join(medidozeDir, 'config2.json'), 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                self.serverSetUpDone.emit(config,connectionString)
                self.createTables()
            else:
                if connection_result['error']:
                    print(connection_result['error'])
                else:
                    print("Connection timed out")
                self.infoServerConfig.setText("Error connecting to server. Please check your server details.")
                self.infoServerConfig.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:10px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
                QTimer.singleShot(4000, self.clear_info_messages)
                return

        except Exception as e:
            self.infoServerConfig.setText("Something went wrong. Please try again.")
            self.infoServerConfig.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:10px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
            QTimer.singleShot(4000, self.clear_info_messages)
            print(e)
            print()

    def createTables(self):
        try:
            print("================ Creating Tables.... ================")
            local_cursor = self.local_conn.cursor()
            columns = [
                'uid VARCHAR(50) PRIMARY KEY',
                'password VARCHAR(64) NOT NULL',
                'firstName VARCHAR(30) NOT NULL',
                'lastName VARCHAR(20) NOT NULL',
                'phone BIGINT NOT NULL',
                'image TEXT',
                'isAdmin CHAR(1) NOT NULL',
                'isActive CHAR(1) NOT NULL',
                'isSoftDlt CHAR(1) NOT NULL',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL',
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users') CREATE TABLE users ({', '.join(columns)})")

            columns = [
                    'id INT PRIMARY KEY IDENTITY',
                    'date_of_dispense VARCHAR(50) NOT NULL',
                    'patient_first_name VARCHAR(30) NOT NULL',
                    'patient_last_name VARCHAR(20) NOT NULL',
                    'rx_number VARCHAR(20) NOT NULL',
                    'route VARCHAR(20) NOT NULL',
                    'drug VARCHAR(20) NOT NULL',
                    'pharmacist_full_name VARCHAR(20) NOT NULL',
                    'pharmacist_short_name VARCHAR(20) NOT NULL',
                    'stop_date VARCHAR(20) NOT NULL',
                    'supply_type VARCHAR(20) NOT NULL',
                    'filling_status BIT NOT NULL DEFAULT 1',
                    'createdBy VARCHAR(50) NOT NULL',
                    'updatedBy VARCHAR(50) NOT NULL',
                    'createdDate DATETIME NOT NULL',
                    'updatedDate DATETIME NOT NULL'
                ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'logs') CREATE TABLE logs ({', '.join(columns)})")

            columns = [
                'id BIGINT PRIMARY KEY',
                'route VARCHAR(20)',
                'firstName VARCHAR(30)',
                'lastName VARCHAR(30)',
                'areaCode INT',
                'phone BIGINT',
                'image TEXT',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL', 
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'patient') CREATE TABLE patient ({', '.join(columns)})")

            columns = [
                'id INT PRIMARY KEY IDENTITY',
                'dlpatientID BIGINT',
                'dlPatientFirstName VARCHAR(30)',
                'dlPatientLastName VARCHAR(30)',
                'dlRxID INT',
                'dlDrug VARCHAR(50)',
                'dlMedicationID INT',
                'dlDose FLOAT',
                'dlReefDate DATETIME NOT NULL',
                'dlDispenseDate DATETIME NOT NULL',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL', 
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dispenseLogs') CREATE TABLE dispenseLogs ({', '.join(columns)})")

            columns = [
                'id INT PRIMARY KEY IDENTITY',
                'idlMedicationID INT',
                'idlDose FLOAT',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL', 
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'instantDoseLogs') CREATE TABLE instantDoseLogs ({', '.join(columns)})")

            print("================ Tables Created ================")

            current_datetime=datetime.now()
            createdDate = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            admin_password = sha256("admin".encode()).hexdigest()
            super_admin_pass = sha256("a".encode()).hexdigest()
            
            query = f"IF NOT EXISTS (SELECT 1 FROM users WHERE uid = 'sys') INSERT INTO users (uid, password, firstName, lastName, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
            local_cursor.execute(query, ('sys', super_admin_pass, 'Super', 'Admin', '', 'Y', 'Y', 'N', 'Super Admin', 'Super Admin', createdDate, createdDate))
            print("================ Super Admin Added ================")

            query = f"IF NOT EXISTS (SELECT 1 FROM users WHERE uid = 'admin') INSERT INTO users (uid, password, firstName, lastName, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate) VALUES ('admin','{admin_password}','Medidoze Technologies','','', 'Y', 'Y', 'N', 'Super Admin', 'Super Admin', '{createdDate}', '{createdDate}')"
            local_cursor.execute(query)
            print("================ Admin Added ================")
            self.local_conn.commit()
            local_cursor.close()
        except Exception as e:
            print(e)
            local_cursor.rollback()
            local_cursor.close()

    def clear_info_messages(self):
        try:
            self.infoServerConfig.setText("")
            self.infoServerConfig.setStyleSheet("background:none;padding:10px;")
        except Exception as e:
            print(e)


