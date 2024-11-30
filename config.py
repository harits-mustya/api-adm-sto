import os
import pyodbc

def get_odbc_driver(driver_env_variable: str) -> str:
    # Fetch the driver from environment variable (if specified)
    requested_driver = os.getenv(driver_env_variable)
    
    # Get list of available ODBC drivers
    available_drivers = [driver for driver in pyodbc.drivers()]
    
    # If the requested driver is in the available drivers, return it
    if requested_driver in available_drivers:
        return requested_driver
    else:
        # If requested driver is not found, fallback to a common driver
        if "ODBC Driver 17 for SQL Server" in available_drivers:
            return "ODBC Driver 17 for SQL Server"
        elif "SQL Server" in available_drivers:
            return "SQL Server"
        else:
            # Raise error if no suitable driver is found
            raise RuntimeError(f"Driver '{requested_driver}' not found, and no fallback drivers are available.")

# API Key
SECRET_KEY = "customer_satisfaction"

# DB Connection for MASTER USER
AUTH_DB_DRIVER = get_odbc_driver("AUTH_DB_DRIVER")
AUTH_DB_SERVER = os.getenv("AUTH_DB_SERVER", "PUT YOUR DB SERVER")
AUTH_DB_NAME = os.getenv("AUTH_DB_NAME", "PUT YOUR NAME DB SERVER")
AUTH_DB_USERNAME = os.getenv("AUTH_DB_USERNAME", "USERNAME")
AUTH_DB_PASSWORD = os.getenv("AUTH_DB_PASSWORD", "P4SSW0RD")

# DB Connection for STRUCTURE ORGANIZATION
INFO_DB_DRIVER = get_odbc_driver("INFO_DB_DRIVER")
INFO_DB_SERVER = os.getenv("INFO_DB_SERVER", "PUT YOUR DB SERVER")
INFO_DB_NAME = os.getenv("INFO_DB_NAME", "PUT YOUR NAME DB SERVER")
INFO_DB_USERNAME = os.getenv("INFO_DB_USERNAME", "USERNAME")
INFO_DB_PASSWORD = os.getenv("INFO_DB_PASSWORD", "P@SSW0RD")
