# Global configuration variables (simple camelCase)
config = None
localConn = None
liveConn = None
userData = None

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