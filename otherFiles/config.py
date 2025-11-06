# Global configuration variables (simple camelCase)
config = None
localConn = None
liveConn = None
userData = None
pcbComPort = None
leftPumpMedication = None
rightPumpMedication = None
leftPumpCalibrated = False
rightPumpCalibrated = False

def setLocalConfig(configData, localConnData):
    """Initialize global configuration"""
    global config, localConn
    config = configData
    localConn = localConnData
    print(f"Local Config Set - config: {config}, localConn: {localConn is not None}")

def updateLiveConn(liveConnData):
    global liveConn
    liveConn = liveConnData
    print(f"Live connection updated - liveConn: {liveConn is not None}")

def updateUserData(newUserData):
    """Update user data"""
    global userData
    userData = newUserData
    print(f"User data updated: {userData}")

def updatePcbComPort(pcbComPortData):
    global pcbComPort
    pcbComPort = pcbComPortData["device"]
    print(f"PCB com port updated: {pcbComPort}")

def updatePumpMedication(pumpPosition, medication):
    global leftPumpMedication, rightPumpMedication
    if pumpPosition == 'Left':
        leftPumpMedication = medication
    elif pumpPosition == 'Right':
        rightPumpMedication = medication
    print(f"{pumpPosition} Pump medication updated: {medication}")

def updatePumpCalibrated(pumpPosition):
    global leftPumpCalibrated, rightPumpCalibrated
    if pumpPosition == 'Left':
        leftPumpCalibrated = True
    elif pumpPosition == 'Right':
        rightPumpCalibrated = True
    print(f"Pump {pumpPosition} calibrated: True")
