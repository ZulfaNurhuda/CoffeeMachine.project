"""
This utility file provides a function for handling user input with a timeout.
This is crucial for the coffee machine application to prevent it from waiting
indefinitely for user input, allowing it to reset to the main menu after a
period of inactivity.
"""

from inputimeout import inputimeout, TimeoutOccurred
from credentials.config import Configuration
from apps.database.database_manager import DatabaseManager

def input_with_timeout(db_manager: DatabaseManager, text: str, time_limit: int = Configuration.TIMEOUT_DURATION) -> str:
    """
    Takes input from the user with a time limit.

    If the user does not provide input within the specified time limit, it catches
    the `TimeoutOccurred` exception, prints a message, and restarts the main
    simulation loop of the coffee machine.

    Args:
        db_manager (DatabaseManager): The database manager instance, needed to restart the simulation.
        text (str): The text to be displayed as the input prompt.
        time_limit (int): The time limit in seconds (default: TIMEOUT_DURATION from Configuration).

    Returns:
        str: The user's input, or it triggers a simulation restart on timeout.
    """
    try:
        return inputimeout(prompt=text, timeout=time_limit)
    except TimeoutOccurred:
        print(
            "\n⏳ - Waktu habis! Tidak ada aktivitas selama 1 menit. Kembali ke menu utama!.\n"
        )
        from apps.coffee_machine.coffee_machine import CoffeeMachine
        CoffeeMachine(db_manager).simulation()
