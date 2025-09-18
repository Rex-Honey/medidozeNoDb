import os,pyodbc,json,threading,time
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QTimer
from datetime import datetime
from hashlib import sha256
from PyQt6.QtCore import QStandardPaths
from otherFiles.common import setState

class ServerConfigWindow(QWidget):
    serverSetUpDone = pyqtSignal(dict,str)
    def __init__(self):
        super().__init__()
        rootDir=os.path.dirname(os.path.dirname(__file__))
        uic.loadUi(os.path.join(rootDir, 'uiFiles', 'serverConfig.ui'), self)
        self.btnConnect.clicked.connect(self.connectServer)
        for wid in (self.txtServerIP,self.txtServerName,self.txtPort,self.txtUsername,self.txtPassword):
            setState(wid,"ok")

    def connectServer(self):
        try:
            fields = [
                (self.txtServerIP, self.errServerIP, "Server IP Name can't be blank"),
                (self.txtServerName, self.errServerName, "Server Name can't be blank"),
                (self.txtPort, self.errTcpPort, "Port Number can't be blank"),
                (self.txtUsername, self.errUsername, "Username can't be blank"),
                (self.txtPassword, self.errPassword, "Password can't be blank"),
            ]

            fieldsEmpty=False
            for widget, error_label, error_msg in fields:
                setState(widget, "ok")
                error_label.setText("")
                if widget.text().strip() == "":
                    setState(widget, "err")
                    error_label.setText(error_msg)
                    fieldsEmpty=True
            if fieldsEmpty:
                return

            serverIP=self.txtServerIP.text()
            serverPort=self.txtPort.text()
            serverName=self.txtServerName.text()
            username=self.txtUsername.text()
            password=self.txtPassword.text()
            localDatabase="medidozeSyncMedAI"

            # serverIP="192.168.29.151"
            # serverPort="1433"
            # serverName="SQLEXPRESS"
            # username="sa"
            # password="dexter"

            config={
                    "server":f"{serverIP},{serverPort}\\{serverName}",
                    "local_database":localDatabase,
                    "username":f"{username}",
                    "password":f"{password}",
                    "calibrationDateLeft":"",
                    "calibrationDateRight":"",
                    "oatRxPharmacyId":"",
                    "webhookFillApiUrl":"",
                    "oatRxGetAiDatesApiUrl":"",
                    "oatApiToken":""
            }
            
            connectionString = (
                "DRIVER={SQL Server};"
                'SERVER='f"{serverIP},{serverPort}\\{serverName};"
                "DATABASE="f"{localDatabase};"
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
            conn_thread.join(timeout=1)
            
            if connection_result['success']:
                self.local_conn = connection_result['connection']
                self.config=config
                print("Connection successful!")
                createTablesResult = self.createTables()
                if createTablesResult['status'] == 'error':
                    self.infoServerConfig.setText("Something went wrong")
                    self.infoServerConfig.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:10px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
                    QTimer.singleShot(4000, self.clear_info_messages)
                    return
                documentsDir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
                medidozeDir = os.path.join(documentsDir, 'medidoze')
                os.makedirs(medidozeDir, exist_ok=True)
                with open(os.path.join(medidozeDir, 'configAI.json'), 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                self.serverSetUpDone.emit(config,connectionString)
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
            current_datetime=datetime.now()
            createdAt = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

            local_cursor = self.local_conn.cursor()
            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'pharmacyDetails') CREATE TABLE pharmacyDetails(
                OatRxPharmacyId VARCHAR(20),
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL,
                updatedDate DATETIME NOT NULL
            )""")
            print("-- PharmacyDetails table query executed")

            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users') CREATE TABLE users (
                uid VARCHAR(50) PRIMARY KEY,
                oatRxId BIGINT,
                password VARCHAR(64) NOT NULL,
                otp VARCHAR(64),
                firstName VARCHAR(30) NOT NULL,
                lastName VARCHAR(20) NOT NULL,
                phone BIGINT,
                image TEXT,
                isAdmin CHAR(1) NOT NULL,
                isActive CHAR(1) NOT NULL,
                isSoftDlt CHAR(1) NOT NULL,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL,
                updatedDate DATETIME NOT NULL
            )""")
            print("-- Users table query executed")

            super_admin_pass = sha256("a".encode()).hexdigest()
            query = f"IF NOT EXISTS (SELECT 1 FROM users WHERE uid = 'sys') INSERT INTO users (uid, password, firstName, lastName, phone, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate) VALUES ('sys','{super_admin_pass}','Super','Admin', NULL, '', 'Y', 'Y', 'N', 'Super Admin', 'Super Admin', '{createdAt}', '{createdAt}')"
            local_cursor.execute(query)
            print("-- Sys user added query executed")

            admin_password = sha256("admin".encode()).hexdigest()
            query = f"IF NOT EXISTS (SELECT 1 FROM users WHERE uid = 'admin') INSERT INTO users (uid, password, firstName, lastName, phone, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate) VALUES ('admin','{admin_password}','Medidoze Technologies','', NULL, '', 'Y', 'Y', 'N','Super Admin', 'Super Admin', '{createdAt}', '{createdAt}')"
            local_cursor.execute(query)
            print("-- Admin user added query executed")

    # =============================================== din_groups ===============================================
            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'din_groups') CREATE TABLE din_groups (
                id INT PRIMARY KEY IDENTITY,
                medication VARCHAR(50) NOT NULL,
                pump_type VARCHAR(50) NOT NULL,
                pump_position VARCHAR(50),
                status BIT NOT NULL DEFAULT 1,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL,
                updatedDate DATETIME NOT NULL
            )""")
            print("-- Din_groups table query executed")

            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'din') CREATE TABLE din (
                id INT PRIMARY KEY IDENTITY,
                din_number BIGINT NOT NULL,
                strength VARCHAR(20) NOT NULL,
                din_group_id INT NOT NULL,
                status BIT NOT NULL DEFAULT 1,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL,
                updatedDate DATETIME NOT NULL
            )""")
            print("-- Din table query executed")

            query = f"IF NOT EXISTS (SELECT 1 FROM din_groups WHERE medication = ?) INSERT INTO din_groups (medication, pump_type, pump_position, status, createdBy, updatedBy, createdDate, updatedDate) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            local_cursor.execute(query, ('Metadol','Metadol', 'Double', 'Left', 1, 'Super Admin', 'Super Admin', createdAt, createdAt))
            lastRowId = local_cursor.fetchone()[0]
            print("-- DinGourp1 query executed")

            # ['67000005','67000006','67000007','67000008','67000013','67000014','67000015','67000016','66999997','66999998','66999999','67000000','67000001','67000002','67000003','67000004','2394596']
            dinDetails = [(67000005,lastRowId,'10mg'),(67000006,lastRowId,'10mg'),(67000007,lastRowId,'10mg'),(67000008,lastRowId,'10mg'),(67000013,lastRowId,'10mg'),(67000014,lastRowId,'10mg'),(67000015,lastRowId,'10mg'),(67000016,lastRowId,'10mg')]
            for din, dinGroupId, strength in dinDetails:
                query = f"IF NOT EXISTS (SELECT 1 FROM din WHERE din_number = ?) INSERT INTO din (din_number, strength, din_group_id, status, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                local_cursor.execute(query, (din,din, strength, dinGroupId, 1, 'Super Admin', 'Super Admin', createdAt, createdAt))
            print("-- DinGourp1 dins query executed")

            query = f"IF NOT EXISTS (SELECT 1 FROM din_groups WHERE medication = ?) INSERT INTO din_groups (medication, pump_type, pump_position, status, createdBy, updatedBy, createdDate, updatedDate) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            local_cursor.execute(query, ('Methadose', 'Methadose', 'Double', 'Right', 1, 'Super Admin', 'Super Admin', createdAt, createdAt))
            lastRowId = local_cursor.fetchone()[0]
            print("-- DinGourp2 query executed")

            dinDetails = [(66999997,lastRowId,'10mg'),(66999998,lastRowId,'10mg'),(66999999,lastRowId,'10mg'),(67000000,lastRowId,'10mg'),(67000001,lastRowId,'10mg'),(67000002,lastRowId,'10mg'),(67000003,lastRowId,'10mg'),(67000004,lastRowId,'10mg'),(2394596,lastRowId,'10mg')]
            for din, dinGroupId, strength in dinDetails:
                query = f"IF NOT EXISTS (SELECT 1 FROM din WHERE din_number = ?) INSERT INTO din (din_number, strength, din_group_id, status, createdBy, updatedBy, createdDate, updatedDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                local_cursor.execute(query, (din,din, strength, dinGroupId, 1, 'Super Admin', 'Super Admin', createdAt, createdAt))
            print("-- DinGourp2 dins query executed")
    # =============================================== din ======================================================
            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'patient') CREATE TABLE patient (
                id INT PRIMARY KEY IDENTITY,
                dlpatientID BIGINT,
                dlPatientFirstName VARCHAR(30),
                dlPatientLastName VARCHAR(30),
                gender CHAR(1),
                areaCode INT,
                phone BIGINT,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL, 
                updatedDate DATETIME NOT NULL
            )""")
            print("-- Patient table query executed")

            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'refill') CREATE TABLE refill (
                id INT PRIMARY KEY IDENTITY,
                patientID BIGINT,
                medDate DATETIME NOT NULL,
                stopDate DATETIME NOT NULL,
                din BIGINT NOT NULL,
                drugName VARCHAR(50) NOT NULL,
                sig TEXT NOT NULL,
                rxNo INT NOT NULL,
                fillQty FLOAT NOT NULL,
                doctorName VARCHAR(50) NOT NULL,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdAt DATETIME NOT NULL, 
                updatedAt DATETIME NOT NULL
            )""")
            print("-- Refills table query executed")

            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dispenseLogs') CREATE TABLE dispenseLogs (
                id INT PRIMARY KEY IDENTITY,
                dlpatientID BIGINT,
                dlPatientFirstName VARCHAR(30),
                dlPatientLastName VARCHAR(30),
                dlRxID INT,
                dlDrug VARCHAR(50),
                dlMedicationID INT,
                dlDose FLOAT,
                dlReefDate DATETIME NOT NULL,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL, 
                updatedDate DATETIME NOT NULL
            )""")
            print("-- DispenseLogs table query executed")

            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'instantDoseLogs') CREATE TABLE instantDoseLogs (
                id INT PRIMARY KEY IDENTITY,
                idlMedicationID INT,
                idlDose FLOAT,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdDate DATETIME NOT NULL, 
                updatedDate DATETIME NOT NULL
            )""")
            print("-- InstantDoseLogs table query executed")

            local_cursor.execute(f"""IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'qr') CREATE TABLE qr (
                id INT PRIMARY KEY IDENTITY,
                qrCode VARCHAR(10) NOT NULL,
                qrData TEXT NOT NULL,
                createdBy VARCHAR(50) NOT NULL,
                updatedBy VARCHAR(50) NOT NULL,
                createdAt DATETIME NOT NULL,
                updatedAt DATETIME NOT NULL
            )""")
            print("-- Qr table query executed")


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

            query = f"IF NOT EXISTS (SELECT 1 FROM pharmacyDetails) INSERT INTO pharmacyDetails (OatRxPharmacyId, createdBy, updatedBy, createdDate, updatedDate) VALUES ('', 'Super Admin', 'Super Admin', '{createdAt}', '{createdAt}')"
            local_cursor.execute(query)
            print("-- Super Admin added query executed")
            
            self.local_conn.commit()
            local_cursor.close()
            print("================ Tables Created ================")
            return {'status':'success','message':'Tables Created Successfully'}
        except Exception as e:
            print(e)
            local_cursor.rollback()
            local_cursor.close()
            return {'status':'error','message':str(e)}

    def clear_info_messages(self):
        try:
            self.infoServerConfig.setText("")
            self.infoServerConfig.setStyleSheet("background:none;padding:10px;")
        except Exception as e:
            print(e)


