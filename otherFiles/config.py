# Global configuration variables (simple camelCase)
config = None
connString = None
userData = None
medidozeDir = None
localConn = None

def initializeConfig(configData, connStringData, userDataData, medidozeDirData, localConnData):
    """Initialize global configuration"""
    global config, connString, userData, medidozeDir, localConn
    config = configData
    connString = connStringData
    userData = userDataData
    medidozeDir = medidozeDirData
    localConn = localConnData
    print(f"Config initialized - config: {config is not None}, localConn: {localConn is not None}")

def updateUserData(newUserData):
    """Update user data"""
    global userData
    userData = newUserData
    print(f"User data updated: {userData}")

def updateConfig(newConfig, newConnString, newLocalConn):
    """Update configuration"""
    global config, connString, localConn
    config = newConfig
    connString = newConnString
    localConn = newLocalConn

def isConfigInitialized():
    """Check if config is properly initialized"""
    return config is not None and localConn is not None