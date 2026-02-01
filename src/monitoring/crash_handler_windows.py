"""
Crash Handler (Windows)
Placeholder for platform-specific context capture (SEH).
"""

def install_seh_handler():
    """
    On Windows, structured exception handling is best managed 
    at the native level. In v1.0, we rely on the OS-assigned 
    exit codes which are captured by the parent process.
    """
    pass

def get_exception_info():
    """Returns details about the last exception."""
    return {}
