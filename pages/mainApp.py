from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, QStandardPaths
from otherFiles.common import dictfetchall
from pages.pageContainer import PageContainer
from pages.dashboard import DashboardWindow
from pages.dispense import DispenseWindow
from pages.din import DinWindow
from pages.calibration import CalibrationWindow
from pages.primePump import PrimeWindow
from pages.patients import PatientsWindow
from pages.pharmacyUsers import PharmacyUsersWindow
from pages.instantDose import InstantDoseWindow
from pages.settingsAuth import SettingsAuthWindow
from pages.settings import SettingsWindow
import pyodbc, os


class MainAppWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()

    def initUI(self):
        moduleDir = os.path.dirname(os.path.dirname(__file__))
        self.medidozeDir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation), 'medidoze')

        # Main layout: sidebar + main content
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)

        # Sidebar
        sidebarWidget = QWidget()
        sidebarWidget.setObjectName("SidebarWidget")
        sidebarWidget.setFixedWidth(260)
        sidebarLayout = QVBoxLayout(sidebarWidget)
        sidebarLayout.setContentsMargins(10, 10, 10, 10)
        sidebarLayout.setSpacing(0)

        # Logo
        logo = QLabel()
        logo.setObjectName("SidebarLogo")
        logoPixmap = QPixmap(os.path.join(moduleDir, "images", "dashboardLogo.png"))
        logo.setPixmap(logoPixmap)
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        sidebarLayout.addWidget(logo)
        sidebarLayout.addSpacing(20)
        sidebarLayout.addWidget(self._divider())
        sidebarLayout.addSpacing(10)

        # Sidebar buttons (icon, label) - Store window classes instead of instances
        self.buttons = []
        self.sidebarItems = [
            ("Dashboard", "dash.png", DashboardWindow),
            ("Dispense", "dispense.png", DispenseWindow),
            ("Instant Dose", "dispense.png", InstantDoseWindow),
            ("Prime Pump", "dispense.png", PrimeWindow),
            ("Calibrate Pump", "dispense.png", CalibrationWindow),
            ("Patients", "patient_icon.png", PatientsWindow),
            ("DIN Management", "list.svg", DinWindow),
            ("Pharmacy Users", "users.svg", PharmacyUsersWindow),
            ("Stock Management", "list.svg", PrimeWindow),
            ("Reports", "list.svg", PrimeWindow),
            ("Settings", "setting.svg", "settings"),
            ("Logout", "logout.svg", PrimeWindow),
        ]

        self.stack = QStackedLayout()
        
        for idx, (label, iconFile, windowClass) in enumerate(self.sidebarItems):
            btn = QPushButton(f"  {label}")
            btn.setIcon(QIcon(os.path.join(moduleDir, "images", iconFile)))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setProperty("sidebarButton", True)  # For QSS
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.switchPage(i))
            sidebarLayout.addWidget(btn)
            self.buttons.append(btn)

        sidebarLayout.addStretch()

        # Add sidebar and stack to main layout
        mainLayout.addWidget(sidebarWidget)

        contentWidget = QWidget()
        contentWidget.setContentsMargins(0, 0, 0, 0)
        contentWidget.setLayout(self.stack)
        contentWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mainLayout.addWidget(contentWidget, stretch=1)
        self.setLayout(mainLayout)
        
        # Initialize the first page after UI is fully set up
        self.switchPage(0)

    def _divider(self):
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #2b5e9e; margin: 8px 0;")
        return line

    def switchPage(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        
        # Handle settings page specially
        if index == 10:  # Settings page
            self._handleSettingsPage()
            return
        
        # Create a fresh instance every time the button is clicked
        label, iconFile, windowClass = self.sidebarItems[index]
        pageWidget = windowClass()  # No parameters needed
        pageContainer = PageContainer(label, pageWidget)
        
        # Clear the stack and add the new page
        while self.stack.count() > 0:
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        
        self.stack.addWidget(pageContainer)
        self.stack.setCurrentWidget(pageContainer)

    def _handleSettingsPage(self):
        """Handle the settings page with authentication check"""
        try:
            # Import config inside method to get current values
            from otherFiles.config import localConn, userData
            
            # Check if config is available
            if localConn is None or userData is None:
                print("Config not available in _handleSettingsPage")
                return
                
            # Check if user has OTP set
            local_cursor = localConn.cursor()
            query = "SELECT * FROM users WHERE uid = ?"
            local_cursor.execute(query, userData['uid'])
            userDataResult = dictfetchall(local_cursor)
            
            if userDataResult and userDataResult[0]['otp']:
                # User has OTP, show authentication page
                pageWidget = SettingsAuthWindow()  # No parameters needed
                # Connect the authentication success signal
                pageWidget.authenticated.connect(self._switchToSettings)
            else:
                # No OTP, go directly to settings
                self._switchToSettings()
                return  # Exit early since we're switching to settings directly
                
        except Exception as e:
            print(f"Error handling settings page: {e}")
            # Fallback to settings auth page
            pageWidget = SettingsAuthWindow()  # No parameters needed
            pageWidget.authenticated.connect(self._switchToSettings)
        
        # Create page container and add to stack (only if we have a pageWidget)
        pageContainer = PageContainer("Settings", pageWidget)
        
        # Clear the stack and add the new page
        while self.stack.count() > 0:
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        
        self.stack.addWidget(pageContainer)
        self.stack.setCurrentWidget(pageContainer)

    def _switchToSettings(self):
        """Switch to the actual settings page after authentication"""
        try:
            pageWidget = SettingsWindow()  # No parameters needed
            pageContainer = PageContainer("Settings", pageWidget)
            
            # Clear the stack and add the new page
            while self.stack.count() > 0:
                widget = self.stack.widget(0)
                self.stack.removeWidget(widget)
                widget.deleteLater()
            
            self.stack.addWidget(pageContainer)
            self.stack.setCurrentWidget(pageContainer)
            
        except Exception as e:
            print(f"Error switching to settings: {e}")