"""
This file serves as the central definition for data structures (data classes)
used throughout the coffee machine application. Using data classes ensures
data consistency and integrity as it passes through various modules,
such as order management, database interaction, and payment processing.

The data classes defined here include:
- CoffeeData: Stores detailed information about each type of coffee.
- CompositionData: Defines the composition of additives in an order.
- OrderItem: Represents a single item in a user's order cart.
- QRCodeData: Stores data related to QR code payment transactions.
- SalesRecord: A structure for logging each successful sales transaction.
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class CoffeeData:
    """
    Represents coffee data, including basic attributes and metadata
    for synchronization with Google Sheets.

    Attributes:
        name (str): The unique name of the coffee type.
        price (int): The price per serving.
        stock (int): The available stock quantity.
        row_number (int): The row number in Google Sheets for easy updates.
        number (int): The dynamic sequence number displayed on the menu.
    """
    name: str
    price: int
    stock: int
    row_number: int
    number: int = 0

@dataclass
class CompositionData:
    """
    Represents the composition of additives in a single serving of coffee.
    Each attribute stores the amount of the additive selected by the user.

    Attributes:
        sugar (int): The amount of sugar.
        creamer (int): The amount of creamer.
        milk (int): The amount of milk.
        chocolate (int): The amount of chocolate.
    """
    sugar: int
    creamer: int
    milk: int
    chocolate: int

@dataclass
class OrderItem:
    """
    Represents a specific item in a user's order.
    This includes the type of coffee, quantity, temperature, and custom composition.

    Attributes:
        coffee (CoffeeData): The CoffeeData object being ordered.
        quantity (int): The number of servings for this item.
        temperature (str): The selected temperature ('hangat' or 'dingin').
        composition (CompositionData): The selected additive composition.
    """
    coffee: CoffeeData
    quantity: int
    temperature: str
    composition: CompositionData

@dataclass
class QRCodeData:
    """
    Represents data related to a QR payment reference (QRIS).
    Used to track the transaction status from 'Pending' to 'Selesai' or 'Expired'.

    Attributes:
        ref_id (str): The unique ID generated for each QR transaction.
        total_price (int): The amount to be paid.
        payment_method (str): The payment method used (e.g., 'QRIS').
        timestamp (str): The time the transaction was created.
        status (str): The last status of the transaction ('Pending', 'Selesai', 'Expired').
        row_number (int): The row number in Google Sheets for status updates.
    """
    ref_id: str
    total_price: int
    payment_method: str
    timestamp: str
    status: str
    row_number: int = 0

@dataclass
class SalesRecord:
    """
    Represents the complete data of a single sales transaction to be
    logged into the 'DataPenjualan' sheet.

    Attributes:
        coffee_type (str): The name of the coffee sold.
        temperature (str): The temperature of the coffee.
        composition (str): A description of the additive composition.
        quantity (str): The quantity sold (formatted as a string, e.g., 'x1').
        total_price (int): The total price for this item.
        payment_method (str): The payment method used.
    """
    coffee_type: str
    temperature: str
    composition: str
    quantity: str
    total_price: int
    payment_method: str

    def to_dict(self) -> Dict[str, any]:
        """
        Converts the SalesRecord object to a dictionary.
        This is useful for serialization or storing data in a more
        common format like JSON or for sending to an API.

        Returns:
            Dict[str, any]: A dictionary representing the sales data.
        """
        # Recalculate the total price based on the quantity
        try:
            quantity_int = int(self.quantity.replace('x', ''))
        except ValueError:
            quantity_int = 1 # Default if the quantity format is invalid

        return {
            "jenis_kopi": self.coffee_type,
            "suhu": self.temperature,
            "komposisi": self.composition,
            "jumlah": self.quantity,
            "total_harga": self.total_price * quantity_int,
            "metode_pembayaran": self.payment_method
        }
