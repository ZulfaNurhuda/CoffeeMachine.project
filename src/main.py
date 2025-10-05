"""
This is the main entry point for the Coffee Machine application.

This script initializes and runs the core components of the application:
1.  **Database Manager**: It starts by creating an instance of `DatabaseManager`,
    which handles all interactions with the Google Sheets backend, including
    caching and data synchronization.
2.  **Web Service**: It launches a Flask-based web service in a separate thread.
    This web service is responsible for handling QR code payment confirmations.
3.  **Coffee Machine Simulation**: Once the web service is confirmed to be running,
    it starts the main coffee machine simulation loop (`CoffeeMachine.simulasi`),
    which presents the user interface in the console.

The script also handles graceful shutdown using `KeyboardInterrupt` (Ctrl+C),
ensuring that any pending data changes are saved before exiting.
"""

import sys  # Module to access system-specific parameters and functions

sys.path.append("./")  # Add the main directory to the path to allow module imports
sys.dont_write_bytecode = True  # Prevent the creation of .pyc files

import time
import socket
import threading

from apps.database.database_manager import DatabaseManager
from apps.coffee_machine.coffee_machine import CoffeeMachine
from apps.webservice.app import WebApplication
from credentials.config import Configuration

def check_webservice(host: str, port: int) -> bool:
    """
    Checks if the web service is up and running.

    It attempts to establish a socket connection to a specific host and port.

    Args:
        host (str): The host of the web service (e.g., '127.0.0.1').
        port (int): The port of the web service (e.g., 5000).

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # Set a timeout to avoid waiting indefinitely
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, socket.error):
            return False

def main():
    """
    The main function to orchestrate the startup of the coffee machine and web service.
    """
    # Initialize the database manager, which connects to Google Sheets and loads data.
    db_manager = DatabaseManager()

    # Get web service configuration.
    host, check_host, port = Configuration.HOST, Configuration.CHECK_HOST, Configuration.PORT

    def run_webservice():
        """Target function to run the Flask web application."""
        web_app = WebApplication(db_manager)
        web_app.run(host=host, port=port)

    # Start the web service in a daemon thread.
    # This allows the main program to exit even if the web service thread is running.
    web_thread = threading.Thread(target=run_webservice, daemon=True)
    web_thread.start()

    print("Menunggu webservice untuk memulai...")
    # Wait until the web service is confirmed to be running.
    while not check_webservice(host=check_host, port=port):
        time.sleep(1)
    print("Webservice berhasil dijalankan.")

    # Once the web service is running, start the coffee machine simulation.
    coffee_machine = CoffeeMachine(db_manager)
    try:
        coffee_machine.simulation()
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C.
        print("\nCTRL+C ditekan. Menyimpan perubahan dan keluar...")
        db_manager.save_changes_before_exit()
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # This handles the case where Ctrl+C is pressed during startup.
        print("\nProgram dihentikan saat startup. Keluar.")
        sys.exit(0)
