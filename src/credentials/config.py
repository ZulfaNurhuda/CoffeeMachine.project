"""
This file is responsible for loading and providing all configuration variables
for the coffee machine application. It uses the `dotenv` library to load sensitive
information and settings from a `.env` file, separating configuration from code.

This approach enhances security by keeping private credentials out of version control
and makes it easy to modify settings without changing the source code.

Key configurations managed here include:
- Google Sheets API credentials (service account file and sheet ID).
- Default settings like the admin code.
- Network settings for the web service (host and port).
- Time-related settings like input timeouts and synchronization intervals.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# --------------------------------------
#   INITIALIZE ENVIRONMENT VARIABLES
# --------------------------------------
# This section loads private credentials and other settings from a .env file.
# The .env file must be located in the same directory as this file.
#
# The .env file should contain the following variables:
# - SERVICE_ACCOUNT_FILE: The name of the Google service account credentials file (e.g., 'credentials.json').
# - SHEET_ID: The ID of the Google Sheet used for storing transaction data.
#
# This is done to maintain the security and privacy of sensitive information.
# Using a .env file also simplifies configuration management.

ENV_FILE = Path(
    os.path.join(
        os.getcwd(),
        "credentials",
        ".env",
    )
)

if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    print(f"File {ENV_FILE.name} tidak ditemukan. Pastikan file .env ada di direktori yang benar.")
    import sys
    sys.exit(1)

# =============================================================================================================

class Configuration:
    """Global configuration for the coffee machine application."""

    # Google service account credentials file
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.getcwd(),
        "credentials",
        os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json"),
    )

    # Google Sheets ID
    SHEET_ID = os.getenv("SHEET_ID", "123abc456def789ghi012jkl345mno678pqrs")

    # Default admin code (if admin_code.txt does not exist)
    DEFAULT_ADMIN_CODE = 1234567890

    # Host for the web service
    HOST = "0.0.0.0"

    # Port for the Flask web service
    PORT = 5000

    # Host for checking connection (to indicate that the web server is running)
    CHECK_HOST = "127.0.0.1"  # DO NOT CHANGE

    # Timeout duration for input (in seconds)
    TIMEOUT_DURATION = 60

    # Periodic synchronization interval to Google Sheets (in seconds)
    SYNC_INTERVAL = 300  # 5 minutes

    # QRIS payment timeout (in seconds)
    QRIS_TIMEOUT = 300  # 5 minutes
