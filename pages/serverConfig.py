import os,pyodbc,json,threading
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

            try:
                self.local_conn = pyodbc.connect(connectionString)
                self.config=config
                print("Connection successful!")
                documentsDir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
                medidozeDir = os.path.join(documentsDir, 'medidoze')
                os.makedirs(medidozeDir, exist_ok=True)
                with open(os.path.join(medidozeDir, 'config2.json'), 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                self.serverSetUpDone.emit(config,connectionString)
                self.local_conn.close()

            except pyodbc.Error as ex:
                self.infoServerConfig.setText("Error connecting to server")
                self.infoServerConfig.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:10px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
                QTimer.singleShot(4000, self.clear_info_messages)
                sqlstate = ex.args[0]
                print(f"SQL Server error occurred: {sqlstate}")
                print(f"Details: {str(ex)}")
            print()
        except Exception as e:
            print(e)

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
                'medication VARCHAR(50) NOT NULL',
                'pump_type VARCHAR(50) NOT NULL',
                'pump_position VARCHAR(50)',
                'status BIT NOT NULL DEFAULT 1',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL',
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'din_groups') CREATE TABLE din_groups ({', '.join(columns)})")

            columns = [
                'id INT PRIMARY KEY IDENTITY',
                'din_number BIGINT NOT NULL',
                'din_group_id INT NOT NULL',
                'status BIT NOT NULL DEFAULT 1',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL',
                'updatedDate DATETIME NOT NULL',
                # 'FOREIGN KEY (din_group_id) REFERENCES din_groups(id)'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'din') CREATE TABLE din ({', '.join(columns)})")

            columns = [
                'id INT PRIMARY KEY IDENTITY',
                'database_type VARCHAR(50) NOT NULL',
                'server VARCHAR(50) NOT NULL',
                'database_name VARCHAR(50) NOT NULL',
                'username VARCHAR(50) NOT NULL',
                'password VARCHAR(50) NOT NULL',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL',
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'medidoze_databases') CREATE TABLE medidoze_databases ({', '.join(columns)})")

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
                'id INT PRIMARY KEY IDENTITY',
                'rxID INT NOT NULL',
                'patientID BIGINT',
                'rxDrug VARCHAR(50)',
                'rxOrigDate DATETIME',
                'rxStopDate DATETIME',
                'rxQty FLOAT',
                'rxDays INT NOT NULL',
                'rxType VARCHAR(20)',
                'rxDin INT NOT NULL',
                'rxSig VARCHAR(MAX)',
                'rxDrFirst VARCHAR(50)',
                'rxDrLast VARCHAR(50)',
                'scDays VARCHAR(10)',
                'createdBy VARCHAR(50) NOT NULL',
                'updatedBy VARCHAR(50) NOT NULL',
                'createdDate DATETIME NOT NULL', 
                'updatedDate DATETIME NOT NULL'
            ]
            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'rx') CREATE TABLE rx ({', '.join(columns)})")

            local_cursor.execute("""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'refill') CREATE TABLE refill (
                id INT PRIMARY KEY IDENTITY,
                rxID INT NOT NULL,
                patientID BIGINT,
                reefDate DATETIME,
                prevDate DATETIME,
                witness FLOAT,
                carry VARCHAR(50),
                frequency VARCHAR(20) DEFAULT 'OD',
                emergencyCount INT,
                totProcessing FLOAT,
                totRemaining FLOAT,
                reReason CHAR(2),
                reJudge DATETIME,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL, 
                updatedDate DATETIME NOT NULL
            )""")

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

            # columns = [
            #     'id int PRIMARY KEY IDENTITY',
            #     'name VARCHAR(20)',
            #     'date DATETIME'
            # ]
            # local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'TB1') CREATE TABLE TB1 ({', '.join(columns)})")

            # columns = [
            #     'id int PRIMARY KEY',
            #     'tbid INT'
            # ]
            # local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'TB2') CREATE TABLE TB2 ({', '.join(columns)})")

            current_datetime=datetime.now()
            phone=9999999999
            createdDate = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            admin_password = sha256("admin".encode()).hexdigest()
            super_admin_pass = sha256("a".encode()).hexdigest()
            
            query = f"IF NOT EXISTS (SELECT 1 FROM users WHERE uid = 'sys') INSERT INTO users (uid, password, firstName, lastName, phone, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate) VALUES ('sys','{super_admin_pass}','Super','Admin',{phone}, '', 'Y', 'Y', 'N', 'Super Admin', 'Super Admin', '{createdDate}', '{createdDate}')"
            local_cursor.execute(query)

            query = f"IF NOT EXISTS (SELECT 1 FROM users WHERE uid = 'admin') INSERT INTO users (uid, password, firstName, lastName, phone, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate) VALUES ('admin','{admin_password}','Medidoze Technologies','',{phone}, '', 'Y', 'Y', 'N', 'Super Admin', 'Super Admin', '{createdDate}', '{createdDate}')"
            local_cursor.execute(query)

            local_cursor.execute(f"IF NOT EXISTS (SELECT * FROM medidoze_databases where database_type='live') INSERT INTO medidoze_databases (database_type, server, database_name, username, password, createdBy, updatedBy, createdDate, updatedDate) VALUES ('live','{self.config['server']}','','{self.config['username']}', '{self.config['password']}','Super Admin', 'Super Admin', '{createdDate}','{createdDate}')")

            self.local_conn.commit()
            local_cursor.close()
            print("================ Tables Created ================")
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


