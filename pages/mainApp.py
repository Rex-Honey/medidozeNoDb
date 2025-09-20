from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedLayout, QLabel, QSizePolicy, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, QStandardPaths, pyqtSignal
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
    # Signal to notify main window about logout
    logoutRequested = pyqtSignal()
    # Signal to notify when WinRx database is configured
    winRxConfigured = pyqtSignal()
    
    def __init__(self):  # No parameters needed
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

        # Create sidebar based on user role and WinRx configuration
        self.createSidebar(sidebarLayout, moduleDir)

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

    def createSidebar(self, sidebarLayout, moduleDir):
        """Create sidebar based on user role and WinRx configuration"""
        # Create sidebar items
        self._createSidebarItems(sidebarLayout, moduleDir)
        
        # Create stack layout (only during initial creation)
        self.stack = QStackedLayout()

    def refreshSidebar(self):
        """Refresh sidebar when WinRx database is configured"""
        # Clear existing sidebar
        for btn in self.buttons:
            btn.deleteLater()
        self.buttons.clear()
        
        # Get the sidebar widget and its layout
        moduleDir = os.path.dirname(os.path.dirname(__file__))
        sidebarWidget = self.findChild(QWidget, "SidebarWidget")
        if sidebarWidget:
            sidebarLayout = sidebarWidget.layout()
            
            # Remove only the button widgets, preserve logo, dividers, and spacing
            items_to_remove = []
            for i in reversed(range(sidebarLayout.count())):
                item = sidebarLayout.itemAt(i)
                if item:
                    if item.widget():
                        widget = item.widget()
                        # Keep logo and dividers, remove only buttons
                        if (widget.objectName() != "SidebarLogo" and 
                            not widget.objectName().startswith("divider") and
                            isinstance(widget, QPushButton)):
                            items_to_remove.append(i)
                    elif item.spacerItem():
                        # Remove stretch items but keep spacing items
                        spacer = item.spacerItem()
                        # Only remove stretch items (vertical spacers), keep fixed spacing
                        if spacer and spacer.expandingDirections() & Qt.Orientation.Vertical:
                            items_to_remove.append(i)
            
            # Remove items
            for i in items_to_remove:
                item = sidebarLayout.itemAt(i)
                if item:
                    if item.widget():
                        widget = item.widget()  # Store widget reference before removing
                        sidebarLayout.removeWidget(widget)
                        widget.deleteLater()  # Now safe to call deleteLater
                    else:
                        sidebarLayout.removeItem(item)
            
            # Recreate sidebar items
            self._createSidebarItems(sidebarLayout, moduleDir)
            
            # Add stretch at the end to maintain top alignment (same as initial creation)
            sidebarLayout.addStretch()
            
            # Switch to dashboard
            self.switchPage(0)

    def _createSidebarItems(self, sidebarLayout, moduleDir):
        """Create sidebar items without recreating the stack layout"""
        # Import config to check user role and WinRx database
        from otherFiles.config import config, userData
        
        # Check if user is admin
        isAdmin = userData and userData.get('isAdmin') == 'Y'
        
        # Check if WinRx database is configured
        hasWinRxDatabase = config and config.get('winrxDbName') and config.get('winrxDbName').strip()
        
        # Define all possible sidebar items
        allSidebarItems = [
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
            ("Logout", "logout.svg", "logout"),
        ]
        
        # Determine which items to show
        if isAdmin and not hasWinRxDatabase:
            # Admin user without WinRx database - show only Settings and Logout
            self.sidebarItems = [
                ("Settings", "setting.svg", "settings"),
                ("Logout", "logout.svg", "logout"),
            ]
        else:
            # All other cases - show all items
            self.sidebarItems = allSidebarItems
        
        # Create buttons with exact same properties as initial creation
        self.buttons = []
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

    def _divider(self):
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #2b5e9e; margin: 8px 0;")
        return line

    def switchPage(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        
        # Handle settings page specially
        if self.sidebarItems[index][0] == "Settings":
            self._handleSettingsPage()
            return
        
        # Handle logout page specially
        if self.sidebarItems[index][0] == "Logout":
            self._handleLogout()
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

    def _handleLogout(self):
        """Handle logout functionality"""
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                'Logout Confirmation', 
                'Are you sure you want to logout?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Clear global config
                from otherFiles.config import updateUserData
                updateUserData(None)
                
                # Emit signal to main window to switch to sign-in page
                self.logoutRequested.emit()
                
                # Reset button states
                for btn in self.buttons:
                    btn.setChecked(False)
            else:
                # User cancelled logout, uncheck the logout button
                logoutIndex = next((i for i, item in enumerate(self.sidebarItems) if item[0] == "Logout"), -1)
                if logoutIndex >= 0:
                    self.buttons[logoutIndex].setChecked(False)
                
        except Exception as e:
            print(f"Error during logout: {e}")
            # Reset button state on error
            logoutIndex = next((i for i, item in enumerate(self.sidebarItems) if item[0] == "Logout"), -1)
            if logoutIndex >= 0:
                self.buttons[logoutIndex].setChecked(False)

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
            # Connect signal to refresh sidebar when WinRx is configured
            if hasattr(pageWidget, 'winRxConfigured'):
                pageWidget.winRxConfigured.connect(self.refreshSidebar)
            
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