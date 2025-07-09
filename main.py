from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QStackedLayout
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui import QFont, QIcon
import json, pyodbc, sys, os, resr
from pages.sigin import SignInWindow
from pages.serverConfig import ServerConfigWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        module_dir = os.path.dirname(__file__)
        self.setWindowTitle("Medidoze Technologies Inc.")
        self.setWindowIcon(QIcon(os.path.join(module_dir, 'images', 'medidoze-icon.ico')))
        self.setObjectName("mainWindow")

        self.setGeometry(250, 100, 1400, 830)
        self.setFixedSize(1400, 830)

        self.stackLayout = QStackedLayout()
        centralWidget = QWidget()
        centralWidget.setLayout(self.stackLayout)
        self.setCentralWidget(centralWidget)

        self.signInWindow = SignInWindow()
        self.signInWindow.loginSuccess.connect(self.loginSuccess)
        self.stackLayout.addWidget(self.signInWindow)
        self.checkConfig()

    def checkConfig(self):
        try:
            documentsDir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            with open(os.path.join(documentsDir, 'medidoze', 'configN.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
            connString = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['local_database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
            )
            conn = pyodbc.connect(connString)
            print("Connection successful!")
            conn.close()
            self.signInWindow.setConfig(connString)
        except FileNotFoundError:
            print("No JSON config file found.")
            self.serverConfigWindow = ServerConfigWindow()
            self.stackLayout.addWidget(self.serverConfigWindow)
            self.serverConfigWindow.serverSetUpDone.connect(self.serverSetUpDone)
            self.stackLayout.setCurrentWidget(self.serverConfigWindow)
        except Exception as e:
            print(e)
            self.serverConfigWindow = ServerConfigWindow()
            self.stackLayout.addWidget(self.serverConfigWindow)
            self.serverConfigWindow.serverSetUpDone.connect(self.serverSetUpDone)
            self.stackLayout.setCurrentWidget(self.serverConfigWindow)

    def serverSetUpDone(self, config, connString):
        self.stackLayout.setCurrentWidget(self.signInWindow)
        self.signInWindow.setConfig(connString)

    def loginSuccess(self, userData):
        print(f"Login successful: {userData}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application font - this applies to ALL widgets
    font = QFont("Nirmala UI", 9)
    app.setFont(font)
    mainWindow = MainWindow()
    qssPath = os.path.join(os.path.dirname(__file__), 'qss', 'style.qss')
    with open(qssPath, 'r') as f:
        app.setStyleSheet(f.read())
    mainWindow.show()
    sys.exit(app.exec())