# Global configuration variables (simple camelCase)
config = None
localConn = None
userData = None

def setConfig(configData, localConnData):
    """Initialize global configuration"""
    global config, localConn
    config = configData
    localConn = localConnData
    print(f"Config initialized - config: {config}, localConn: {localConn is not None}")

def updateUserData(newUserData):
    """Update user data"""
    global userData
    userData = newUserData
    print(f"User data updated: {userData}")

def isConfigInitialized():
    """Check if config is properly initialized"""
    return config is not None and localConn is not None