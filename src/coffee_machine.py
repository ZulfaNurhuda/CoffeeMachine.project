"""
# ╒==================================================╕
# |        VIRTUAL COFFEE MACHINE SIMULATION         |
# ╘==================================================╛

╭------------╮
| BACKGROUND |
╰------------╯
In today's digital era, computational thinking has become an important skill that students need to possess.
This ability includes problem-solving methods, designing systematic steps, and simplifying complex processes.

One way to apply computational thinking principles in daily life is by creating a coffee machine algorithm simulation.
A coffee machine has structured processes, such as selecting coffee types, determining composition, order quantity,
and handling payments automatically.

╭------------------╮
| PROGRAM FEATURES |
╰------------------╯
Various features available in this coffee machine algorithm include:
1.  Connected to Google Spreadsheet as database,
2.  Can handle multiple orders simultaneously from users,
3.  Customizable menu according to available data,
4.  Can select desired coffee temperature,
5.  Can customize composition of additional ingredients (including sugar, milk, creamer, and chocolate),
6.  Supports two payment methods: cash and QRIS (simulation),
7.  Can create simulation when users have ordered coffee online,
    users only need to show QR code for confirmation,
8.  Detailed and accurate order recording,
9.  Well-organized error handling,
10. Clear information for users at every step,
11. Validation for every user input,
12. Special admin menu secured with admin code, admin menu includes program shutdown
    and coffee restocking.

╭-----------------------------╮
| AUTHORS / ALGORITHM WRITERS |
╰-----------------------------╯
All members of group 13, class 31, Computational Thinking course ITB 2024:
1. Laurenisus Dani Rendragraha      (19624272)
2. Mineva Azzahra                   (19624227)
3. Muhammad Faiz Alfada Dharma      (19624244)
4. Muhammad Zulfa Fauzan Nurhuda    (19624258)
"""

# ╒====================================╕
# |          IMPORT LIBRARIES          |
# ╘====================================╛
# Standard library imports
# System and OS utilities for file operations and program control
import sys
import os
import random
import string
from pathlib import Path

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from functools import lru_cache

# Third-party library imports
# External libraries for Google Sheets, QR code, and input timeout functionality
import gspread
from google.oauth2.service_account import Credentials
from inputimeout import inputimeout, TimeoutOccurred
import cv2
import qrcode_terminal
from dotenv import load_dotenv

# ╒====================================╕
# |     ENVIRONMENT VARIABLE INIT      |
# ╘====================================╛

# Using .env file to store private credentials and other settings.
# The .env file must exist in the same directory as this file.

# The .env file contains the following variables:
# - SERVICE_ACCOUNT_FILE: Google service account credential file name (e.g., 'credentials.json')
# - SHEET_ID: Google Sheets ID used to store transaction data

# This is done to maintain security and privacy of sensitive information.
# Using .env file also facilitates configuration settings and changes without modifying source code.

# Construct path to .env file in credentials directory
file_env = Path(
    os.path.join(
        os.getcwd(),  # Get current working directory
        "credentials",  # Subdirectory containing credentials
        ".env",  # Environment variables file
    )
)

# Load environment variables from .env file
if file_env.exists():
    # Load environment variables if file exists
    load_dotenv(dotenv_path=file_env)
else:
    # Exit program if .env file is not found
    print(f"File {file_env.name} tidak ditemukan. Pastikan file .env ada di direktori yang benar.")
    import sys
    sys.exit(1)

# ╒====================================╕
# |            CONFIGURATION           |
# ╘====================================╛
class Config:
    """
    Configuration class to store program settings.
    
    This class contains all configuration constants used throughout the application,
    including Google Sheets settings, admin authentication, and timeout configurations.
    All sensitive data is loaded from environment variables for security.
    
    Attributes:
        SHEET_ID (str): Google Sheets document ID for database operations
        SERVICE_ACCOUNT_FILE (str): Path to Google service account credentials file
        admin_code (int): Authentication code for admin-only operations
        timeout_duration (int): Maximum time in seconds to wait for user input
    """

    # Google Sheets configuration - loaded from environment variables
    SHEET_ID = os.getenv("SHEET_ID", "123abc456def789ghi012jkl345mno678pq")  # Spreadsheet ID
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.getcwd(),  # Current working directory
        "credentials",  # Credentials subdirectory
        os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json"),  # Service account file
    )
    
    # Admin and timeout settings
    admin_code = 1234567890  # Admin authentication code for restricted operations
    timeout_duration = 60  # Input timeout duration in seconds (1 minute)


# ╒====================================╕
# |            DATA CLASSES            |
# ╘====================================╛
@dataclass
class CoffeeData:
    """
    Data class to store coffee information.
    
    This class represents a single coffee item with all its properties
    including pricing, stock information, and display positioning.
    
    Attributes:
        name (str): The name/type of the coffee (e.g., "Espresso", "Cappuccino")
        price (int): Price of the coffee in Indonesian Rupiah
        stock (int): Current remaining stock quantity available
        row_number (int): Row number in the Google Sheets database for updates
        number (int): Display number in the menu (assigned dynamically)
    """

    name: str  # Coffee name/type identifier
    price: int  # Coffee price in Indonesian Rupiah
    stock: int  # Current remaining stock quantity
    row_number: int  # Corresponding row number in Google Sheets
    number: int = 0  # Display number in menu (assigned when menu is generated)


@dataclass
class Composition:
    """
    Data class to store additional ingredient composition for coffee customization.
    
    This class represents the customizable ingredients that can be added to coffee.
    Each ingredient is measured in portions, with a range of 0-5 portions allowed.
    
    Attributes:
        sugar (int): Number of sugar portions (0-5)
        creamer (int): Number of creamer portions (0-5)
        milk (int): Number of milk portions (0-5)
        chocolate (int): Number of chocolate portions (0-5)
    """

    sugar: int  # Sugar portions (0-5 range)
    creamer: int  # Creamer portions (0-5 range)
    milk: int  # Milk portions (0-5 range)
    chocolate: int  # Chocolate portions (0-5 range)


@dataclass
class OrderItem:
    """
    Data class to store individual order item with complete specifications.
    
    This class represents a single item in a customer's order, containing
    all necessary information for processing, payment, and preparation.
    
    Attributes:
        coffee (CoffeeData): The coffee type being ordered
        quantity (int): Number of cups being ordered
        temperature (str): Desired temperature ("hangat" or "dingin")
        composition (Composition): Custom ingredient composition
    """

    coffee: CoffeeData  # Coffee type and information
    quantity: int  # Number of cups ordered
    temperature: str  # Temperature preference (hot/cold)
    composition: Composition  # Custom ingredient composition


# ╒====================================╕
# |       DATABASE MANAGEMENT          |
# ╘====================================╛
class DatabaseManager:
    """
    Class to manage database operations with Google Sheets.
    
    This class handles all interactions with the Google Sheets database,
    including reading coffee inventory, recording sales, managing QR queue,
    and updating stock levels. It serves as the data access layer for the application.
    
    Attributes:
        inventory_sheet: Google Sheets worksheet for coffee inventory management
        sales_sheet: Google Sheets worksheet for sales transaction records
        qr_queue_sheet: Google Sheets worksheet for QR code order queue
    """

    def __init__(self):
        """
        Initialize connection to Google Sheets.
        
        Sets up authentication using service account credentials and establishes
        connections to all required worksheets in the Google Sheets database.
        
        Raises:
            FileNotFoundError: If service account credentials file is not found
            gspread.exceptions.SpreadsheetNotFound: If spreadsheet ID is invalid
            gspread.exceptions.WorksheetNotFound: If required worksheets don't exist
        """
        # Set up Google Sheets authentication using service account
        credentials = Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE,  # Path to service account JSON file
            scopes=["https://www.googleapis.com/auth/spreadsheets"],  # Required scope for Sheets API
        )
        client = gspread.authorize(credentials)  # Authorize the client with credentials
        
        # Open the spreadsheet and get worksheets
        spreadsheet = client.open_by_key(Config.SHEET_ID)  # Open spreadsheet by ID
        self.inventory_sheet = spreadsheet.worksheet("PersediaanKopi")  # Coffee inventory worksheet
        self.sales_sheet = spreadsheet.worksheet("DataPenjualan")  # Sales data worksheet
        self.qr_queue_sheet = spreadsheet.worksheet("AntrianPesananQR")  # QR order queue worksheet

    def getColumnIndices(self, worksheet: gspread.Worksheet) -> Dict[str, int]:
        """
        Get mapping of column names to column indices.
        
        Creates a dictionary that maps column header names to their corresponding
        column numbers (1-indexed) for easier cell updates in Google Sheets.
        
        Args:
            worksheet (gspread.Worksheet): The worksheet to analyze
            
        Returns:
            Dict[str, int]: Dictionary mapping column names to column indices
            
        Example:
            {"Jenis Kopi": 1, "Harga": 2, "Sisa Persediaan": 3}
        """
        header = worksheet.row_values(1)  # Get first row (header row)
        return {name: idx + 1 for idx, name in enumerate(header)}  # Create name-to-index mapping

    @lru_cache(maxsize=None)
    def getCoffeeData(self) -> Dict[str, CoffeeData]:
        """
        Retrieve coffee data from `PersediaanKopi` sheet.
        
        Fetches all coffee inventory data from Google Sheets and converts it
        into CoffeeData objects. Uses LRU cache for performance optimization.
        
        Returns:
            Dict[str, CoffeeData]: Dictionary mapping coffee names to CoffeeData objects
            
        Note:
            Row numbers start from 2 because row 1 contains headers
        """
        coffee_data = self.inventory_sheet.get_all_records()  # Get all records from inventory sheet
        return {
            row["Jenis Kopi"]: CoffeeData(  # Use coffee name as key
                name=row["Jenis Kopi"],  # Coffee name from sheet
                price=int(row["Harga"]),  # Convert price to integer
                stock=int(row["Sisa Persediaan"]),  # Convert stock to integer
                row_number=i + 2,  # Row number in sheet (header is row 1)
            )
            for i, row in enumerate(coffee_data)  # Iterate through all coffee records
        }

    def updateStock(self, coffee: CoffeeData, sold_quantity: int) -> None:
        """
        Update coffee stock in `PersediaanKopi` sheet.
        
        Decreases the stock quantity in both the Google Sheets database
        and the local CoffeeData object after a successful sale.
        
        Args:
            coffee (CoffeeData): Coffee object to update
            sold_quantity (int): Number of cups sold
            
        Note:
            Stock cannot go below 0 (uses max(0, new_stock) for safety)
        """
        new_stock = max(0, coffee.stock - sold_quantity)  # Calculate new stock (minimum 0)
        self.inventory_sheet.update_cell(coffee.row_number, 3, new_stock)  # Update in Google Sheets
        coffee.stock = new_stock  # Update local object

    def recordSale(
        self, order_item: OrderItem, payment_method: str
    ) -> None:
        """
        Record sale to `DataPenjualan` sheet.
        
        Adds a new row to the sales data worksheet with complete transaction details
        including coffee type, customization, quantity, total price, and payment method.
        
        Args:
            order_item (OrderItem): The order item containing sale details
            payment_method (str): Payment method used ("Tunai", "QRIS", etc.)
            
        Note:
            The composition is formatted as a readable string showing all ingredient portions
        """
        # Format composition details into readable text
        composition_text = (
            f"Gula ({order_item.composition.sugar} takaran), "  # Sugar portions
            f"Susu ({order_item.composition.milk} takaran), "  # Milk portions
            f"Krimer ({order_item.composition.creamer} takaran), "  # Creamer portions
            f"Cokelat ({order_item.composition.chocolate} takaran)"  # Chocolate portions
        )
        # Append new sale record to the sales sheet
        self.sales_sheet.append_row(
            [
                order_item.coffee.name,  # Coffee type
                order_item.temperature.capitalize(),  # Temperature (capitalized)
                composition_text,  # Formatted ingredient composition
                f"x{order_item.quantity}",  # Quantity with 'x' prefix
                order_item.coffee.price * order_item.quantity,  # Total price
                payment_method,  # Payment method used
            ]
        )

    def restockCoffee(self, coffee: CoffeeData, restock_quantity: int) -> None:
        """
        Perform coffee restock in `PersediaanKopi` sheet.
        
        Increases the stock quantity in both the Google Sheets database
        and the local CoffeeData object. Used by admin for inventory management.
        
        Args:
            coffee (CoffeeData): Coffee object to restock
            restock_quantity (int): Number of cups to add to inventory
            
        Note:
            This operation adds to existing stock (does not replace it)
        """
        new_stock = coffee.stock + restock_quantity  # Calculate new stock after restock
        self.inventory_sheet.update_cell(coffee.row_number, 3, new_stock)  # Update in Google Sheets
        coffee.stock = new_stock  # Update local object


# ╒====================================╕
# |          INPUT UTILITIES           |
# ╘====================================╛
def inputWithTimeout(text: str, timeout_limit: int = Config.timeout_duration) -> str:
    """
    Function to get user input with timeout limit.
    
    Displays a prompt and waits for user input with a specified timeout.
    If no input is received within the timeout period, automatically restarts
    the coffee machine simulation to prevent idle state.
    
    Args:
        text (str): The prompt message to display to the user
        timeout_limit (int): Maximum time to wait for input (in seconds).
                           Defaults to Config.timeout_duration (60 seconds)
        
    Returns:
        str: User input received within the timeout period
        
    Raises:
        TimeoutOccurred: When no input is received within timeout_limit,
                        triggers automatic restart of coffee machine
                        
    Note:
        Uses inputimeout library for cross-platform timeout functionality.
        On timeout, creates new CoffeeMachine instance and restarts simulation.
    """
    try:
        return inputimeout(prompt=text, timeout=timeout_limit)
    except TimeoutOccurred:
        print(
            "\n⏳ - Waktu habis! Tidak ada aktivitas selama 1 menit. Mesin kopi otomatis berhenti.\n\n"
        )
        # Restart the coffee machine when timeout occurs
        coffee_machine = CoffeeMachine()
        coffee_machine.runCoffeeMachineSimulation()


# ╒====================================╕
# |          MENU MANAGEMENT           |
# ╘====================================╛
class MenuManager:
    """
    Class to manage coffee menu display and selection.
    
    Handles the presentation of available coffee options to users,
    assigns selection numbers to each coffee type, and manages the
    coffee menu interface. Works with coffee data to display current
    inventory and availability.
    
    Attributes:
        coffee_list (Dict[str, CoffeeData]): Dictionary mapping coffee names to CoffeeData objects
    """

    def __init__(self, coffee_list: Dict[str, CoffeeData]):
        """
        Initialize menu manager with coffee data.
        
        Sets up the menu manager with the provided coffee inventory data
        for display and selection purposes.
        
        Args:
            coffee_list (Dict[str, CoffeeData]): Dictionary of available coffee options
        """
        self.coffee_list = coffee_list

    def assignCoffeeNumbers(self) -> None:
        """
        Assign display numbers to each available coffee.
        
        Iterates through the coffee list and assigns sequential numbers
        to each coffee that has stock available. These numbers are used
        for user selection in the menu interface.
        
        Note:
            Only coffees with stock > 0 receive display numbers
        """
        number = 1
        for coffee in self.coffee_list.values():
            if coffee.stock > 0:
                coffee.number = number
                number += 1

    def displayCoffeeMenu(self) -> None:
        """
        Display available coffee menu.
        
        Prints a formatted menu showing all available coffee options
        with their assigned numbers, names, prices, and current stock levels.
        Only displays coffees that are currently in stock.
        
        Output format:
            Number. Coffee Name - Price - Stock: Quantity
        """
        print("================ Menu Kopi =================")
        for coffee in self.coffee_list.values():
            if coffee.stock > 0:
                print(
                    f"{coffee.number}. {coffee.name} - Rp{coffee.price} - Persediaan: {coffee.stock}"
                )
        print("=============================================")


# ╒====================================╕
# |         ORDER MANAGEMENT           |
# ╘====================================╛
class OrderManager:
    """
    Class to manage coffee ordering process.
    
    Handles the complete order workflow including coffee selection,
    temperature choice, ingredient customization, quantity determination,
    and order management. Maintains functionality for order merging,
    validation, and summary display.
    
    Attributes:
        coffee_list (Dict[str, CoffeeData]): Available coffee options
        menu_manager (MenuManager): Menu display and management handler
    """

    def __init__(self, coffee_list: Dict[str, CoffeeData], menu_manager: MenuManager):
        """
        Initialize order manager with coffee data and menu manager.
        
        Sets up the order manager with available coffee options
        and menu management capabilities for the ordering process.
        
        Args:
            coffee_list (Dict[str, CoffeeData]): Dictionary of available coffees
            menu_manager (MenuManager): Menu display and management handler
        """
        self.coffee_list = coffee_list
        self.menu_manager = menu_manager

    def selectTemperature(self, coffee_name: str) -> Optional[str]:
        """
        Select coffee temperature (hot or cold).
        
        Displays temperature options and prompts user to choose between
        hot (hangat) or cold (dingin) coffee. Validates input and ensures
        only valid temperature options are accepted. Allows cancellation.
        
        Args:
            coffee_name (str): Name of the coffee for which temperature is being selected
            
        Returns:
            Optional[str]: Selected temperature ("hangat" or "dingin"), or None if cancelled
            
        Note:
            Uses inputWithTimeout to prevent indefinite waiting.
            Loops until valid input is provided or user cancels.
        """
        while True:
            temperature_input = inputWithTimeout(
                f"🌡 - Tentukan suhu untuk {coffee_name}? (1. Hangat | 2. Dingin | 'x' untuk batal): "
            )
            if temperature_input.lower() == "x":
                print("❌ - Membatalkan pemilihan suhu.")
                return None
            elif temperature_input == "1":
                return "hangat"
            elif temperature_input == "2":
                return "dingin"
            else:
                print(
                    "⚠ - Input tidak valid. Silakan masukkan '1' untuk hangat atau '2' untuk dingin."
                )

    def setIngredientAmount(self, ingredient_type: str) -> Optional[int]:
        """
        Set amount of additional ingredient composition (0-5 portions).
        
        Prompts user to specify the amount of a specific ingredient type
        for their coffee customization. Validates input to ensure it falls
        within the acceptable range of 0-5 portions.
        
        Args:
            ingredient_type (str): Type of ingredient being configured
                                 (e.g., "gula", "susu", "krimer", "cokelat")
                                 
        Returns:
            Optional[int]: Number of portions (0-5) if valid input provided,
                          or None if user cancels the operation
                          
        Note:
            - Valid range: 0-5 portions for each ingredient
            - User can type 'x' to cancel ingredient configuration
            - Input validation ensures only integers within range are accepted
        """
        while True:
            amount_input = inputWithTimeout(
                f"> 🎨 - Atur kadar {ingredient_type} (0-5 takaran | 'x' untuk batal): "
            )
            if amount_input.lower() == "x":
                print("❌ - Membatalkan pengaturan komposisi.")
                return None
            try:
                amount = int(amount_input)
                if 0 <= amount <= 5:
                    return amount
                else:
                    print("⚠ - Jumlah harus antara 0 hingga 5.")
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")

    def selectComposition(self) -> Optional[Composition]:
        """
        Select additional ingredient composition.
        
        Prompts user to configure custom amounts for each ingredient type
        (sugar, creamer, milk, chocolate) in their coffee order. Each ingredient
        can be set to 0-5 portions according to user preference.
        
        Returns:
            Optional[Composition]: Composition object with user-specified ingredient amounts,
                                 or None if user cancels the configuration process
                                 
        Note:
            - Sequentially prompts for: sugar, creamer, milk, chocolate
            - Each ingredient accepts 0-5 portions
            - User can cancel at any step by entering 'x'
            - If cancelled, returns None and aborts composition setup
        """
        sugar = self.setIngredientAmount("gula")
        if sugar is None:
            return None
        creamer = self.setIngredientAmount("krimer")
        if creamer is None:
            return None
        milk = self.setIngredientAmount("susu")
        if milk is None:
            return None
        chocolate = self.setIngredientAmount("cokelat")
        if chocolate is None:
            return None
        return Composition(sugar, creamer, milk, chocolate)

    def orderQuantity(self) -> Optional[int]:
        """
        Determine the quantity of coffee to be ordered.
        
        Prompts user to specify how many cups of coffee they want to order
        with the current composition. Validates that the quantity is a positive
        integer and allows user to cancel the order.
        
        Returns:
            Optional[int]: Number of coffee cups to order (positive integer),
                         or None if user cancels the order
                         
        Note:
            - Accepts any positive integer (no upper limit check here)
            - User can type 'x' to cancel the order
            - Input validation ensures only positive integers are accepted
            - Stock validation should be handled elsewhere in the workflow
        """
        while True:
            quantity_input = inputWithTimeout(
                "Pesan berapa kopi dengan komposisi ini? ('x' untuk batal): "  # Quantity prompt
            )
            if quantity_input.lower() == "x":  # Check for cancellation
                print("❌ - Membatalkan pemesanan.\n")  # Cancellation message
                return None
            try:
                quantity = int(quantity_input)  # Convert to integer
                if quantity > 0:  # Validate positive quantity
                    return quantity  # Return valid quantity
                else:
                    print("⚠ - Jumlah kopi harus lebih dari 0.")  # Positive number required message
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")  # Invalid input message

    def isSameComposition(self, comp1: Composition, comp2: Composition) -> bool:
        """
        Compare two additional ingredient compositions.
        
        Checks if two composition objects have identical ingredient amounts
        for all components (sugar, creamer, milk, chocolate). Used for
        order merging when same coffee with same composition is ordered.
        
        Args:
            comp1 (Composition): First composition to compare
            comp2 (Composition): Second composition to compare
            
        Returns:
            bool: True if compositions are identical, False otherwise
            
        Note:
            Uses dataclass equality comparison which checks all fields
        """
        return comp1 == comp2  # Dataclass equality comparison

    def addOrder(
        self,
        order_data: List[OrderItem],
        coffee: CoffeeData,
        temperature: str,
        composition: Composition,
        quantity: int,
    ) -> List[OrderItem]:
        """
        Add order to order list or merge with existing identical order.
        
        Checks if an identical order (same coffee, temperature, and composition)
        already exists in the order list. If found, merges quantities; otherwise,
        creates a new order item and adds it to the list.
        
        Args:
            order_data (List[OrderItem]): Current list of order items
            coffee (CoffeeData): Coffee type being ordered
            temperature (str): Temperature preference ("hangat" or "dingin")
            composition (Composition): Ingredient composition for the coffee
            quantity (int): Number of cups being ordered
            
        Returns:
            List[OrderItem]: Updated order list with new or merged order
            
        Note:
             - Merging occurs when coffee, temperature, and composition match exactly
             - Quantities are combined when orders are merged
             - New OrderItem is created if no matching order exists
         """
        # Check if identical order already exists for merging
        existing = next(
            (
                item
                for item in order_data
                if item.coffee.name == coffee.name
                and item.temperature == temperature
                and self.isSameComposition(item.composition, composition)
            ),
            None,
        )
        if existing:
            existing.quantity += quantity
        else:
            order_data.append(OrderItem(coffee, quantity, temperature, composition))
        return order_data

    def orderSummary(self, orders: List[OrderItem]) -> int:
        """
        Display order summary and calculate total price.
        
        Presents a formatted summary of all items in the order list,
        showing coffee details, quantities, individual prices, and
        ingredient compositions. Calculates and returns the total price.
        
        Args:
            orders (List[OrderItem]): List of order items to summarize
            
        Returns:
            int: Total price of all orders in Indonesian Rupiah
            
        Output format:
            - Header: "Ringkasan Pesanan"
            - Each item: "Number. Coffee (Temperature) xQuantity - Price"
            - Composition: "   Gula: X takaran, Krimer: X takaran, ..."
            - Footer: ">>> Total Harga: RpXXX"
        """
        print("========== Ringkasan Pesanan ==========")  # Order summary header
        total_price = 0  # Initialize total price counter
        # Iterate through each order item with index
        for idx, item in enumerate(orders, 1):
            coffee_price = item.coffee.price * item.quantity  # Calculate item total price
            total_price += coffee_price  # Add to running total
            # Display coffee name, temperature, quantity, and price
            print(
                f"{idx}. {item.coffee.name} ({item.temperature}) x{item.quantity} - Rp{coffee_price}"
            )
            # Display ingredient composition details
            print(
                f"   Gula: {item.composition.sugar} takaran, "  # Sugar portions
                f"Krimer: {item.composition.creamer} takaran, "  # Creamer portions
                f"Susu: {item.composition.milk} takaran, "  # Milk portions
                f"Cokelat: {item.composition.chocolate} takaran"  # Chocolate portions
            )
        print(f">>> Total Harga: Rp{total_price}")  # Display total price
        print("=======================================")  # Summary footer
        return total_price  # Return calculated total

    def selectCoffee(self) -> List[OrderItem]:
        """Handle coffee selection process by user."""
        coffee_name_by_number = {
            coffee.number: coffee for coffee in self.coffee_list.values() if coffee.stock > 0
        }
        order_data: List[OrderItem] = []
        order_number = 1
        while True:
            print(f"\n\n*********** Pesanan ke-{order_number}: Pilih Kopi ************")
            self.menu_manager.displayCoffeeMenu()
            choice = inputWithTimeout("Pilih nomor kopi ('x' untuk batal): ")
            if choice.lower() == "x":
                print("❌ - Membatalkan proses pemesanan.\n")
                order_data = []
                break
            elif choice.isdigit():
                choice_int = int(choice)
                if choice_int in coffee_name_by_number:
                    coffee = coffee_name_by_number[choice_int]
                    print(f"\nAnda memilih {coffee.name}".upper())
                    temperature = self.selectTemperature(coffee.name)
                    if temperature is None:
                        continue
                    composition = self.selectComposition()
                    if composition is None:
                        continue
                    quantity = self.orderQuantity()
                    if quantity is None:
                        continue
                    order_data = self.addOrder(
                        order_data, coffee, temperature, composition, quantity
                    )
                    print("\nApakah Anda ingin memesan kopi lagi?")
                    again = inputWithTimeout(
                        "Ketik 'y' untuk Ya atau 'n' untuk Tidak: "
                    ).lower()
                    if again in ["n", "no", "tidak", "gak"]:
                        print("\nMelanjutkan ke proses pembayaran...")
                        break
                    else:
                        order_number += 1
                else:
                    print("⚠ - Pilihan tidak tersedia. Silakan pilih lagi.")
            else:
                print(
                    "⚠ - Input tidak valid. Silakan masukkan angka atau perintah yang benar."
                )
        return order_data


# ╒====================================╕
# |        PAYMENT MANAGEMENT          |
# ╘====================================╛
class PaymentManager:
    """
    Class to manage payment process.
    
    Handles different payment methods including cash and QRIS payments.
    Provides functionality for payment method selection, transaction processing,
    change calculation, and QR code generation for digital payments.
    
    Supported payment methods:
        - Cash (Tunai): Traditional cash payment with change calculation
        - QRIS: QR code-based digital payment system
    """

    def displayPaymentMethods(self) -> None:
        """
        Display available payment methods.
        
        Shows a formatted menu of payment options available to customers.
        Currently supports cash (Tunai) and QRIS digital payment methods.
        
        Output format:
            1. Tunai (Cash payment)
            2. QRIS (QR code payment)
        """
        print("=== Metode Pembayaran Tersedia ===")  # Payment methods header
        print("1. Tunai")  # Cash payment option
        print("2. QRIS")  # QRIS payment option
        print("===============================")  # Footer

    def processCashPayment(self, total_price: int) -> Tuple[bool, str]:
        """
        Handle cash payment.
        
        Processes cash payment by accepting money input from customer,
        calculating total paid amount, and providing change if necessary.
        Supports partial payments and validates input amounts.
        
        Args:
            total_price (int): Total amount to be paid in Indonesian Rupiah
            
        Returns:
            Tuple[bool, str]: (payment_success, payment_method)
                - payment_success: True if payment completed, False if cancelled
                - payment_method: Always "Tunai" for cash payments
                
        Note:
            - Accepts multiple partial payments until total is reached
            - User can type 'x' to cancel payment at any time
            - Automatically calculates and displays change
            - Validates that input amounts are positive integers
        """
        total_paid = 0  # Track total amount paid so far
        while total_paid < total_price:  # Continue until full payment received
            money_input = inputWithTimeout(
                f"Masukkan uang pembayaran ('x' untuk batal): Rp"  # Payment prompt
            )
            if money_input.lower() == "x":  # Check for cancellation
                print("❌ - Membatalkan pembayaran tunai.\n")  # Cancellation message
                return (False, "Tunai")
            try:
                money = int(money_input)  # Convert input to integer
                if money <= 0:  # Validate positive amount
                    print(
                        "⚠ - Jumlah uang harus lebih besar dari Rp0. Silakan masukkan kembali."  # Invalid amount message
                    )
                    continue
                total_paid += money  # Add to total paid
                if total_paid >= total_price:  # Check if payment complete
                    change = total_paid - total_price  # Calculate change
                    print(
                        f"\n✅ - Pembayaran berhasil. Kembalian Anda: Rp{change}\n"  # Success message with change
                    )
                    return (True, "Tunai")  # Return success
                else:
                    shortage = total_price - total_paid  # Calculate remaining amount
                    print(
                        f"ℹ - Uang kurang. Anda masih kurang Rp{shortage}. Silakan masukkan kembali."  # Shortage message
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")  # Invalid input message
        return (False, "Tunai")  # Fallback return (should not reach here)

    def generateRandomString(self, length: int = 10) -> str:
        """
        Generate random digit string of 'length' characters.
        
        Creates a random string consisting of digits only for use as
        QRIS payment confirmation codes or other verification purposes.
        
        Args:
            length (int): Length of the random string to generate (default: 10)
            
        Returns:
            str: Random string containing only digits (0-9)
            
        Note:
            - Uses only numeric digits for simplicity
            - Default length of 10 provides good security for payment codes
        """
        return "".join(random.choices(string.digits, k=length))  # Generate random digit string

    def generateQrTerminal(self, data: str) -> None:
        """
        Display QR Code in terminal.
        
        Renders a QR code in the terminal using ASCII characters for
        QRIS payment display. The QR code contains the payment data
        that customers can scan with their mobile banking apps.
        
        Args:
            data (str): Data to encode in the QR code (usually payment confirmation code)
            
        Returns:
            None: Displays QR code directly to terminal output
            
        Note:
            - Uses qrcode_terminal library for ASCII QR code rendering
            - QR code is displayed immediately in the terminal
            - Customers scan this code to initiate QRIS payment
        """
        qrcode_terminal.draw(data)  # Display QR code in terminal using ASCII characters

    def processQrisPayment(self, total_price: int) -> Tuple[bool, str]:
        """
        Handle QRIS payment.
        
        Processes QRIS (Quick Response Code Indonesian Standard) payment by
        generating a QR code, displaying it to the customer, and validating
        the confirmation code entered by the customer after payment.
        
        Args:
            total_price (int): Total amount to be paid in Indonesian Rupiah
            
        Returns:
            Tuple[bool, str]: (payment_success, payment_method)
                - payment_success: True if payment completed, False if cancelled/failed
                - payment_method: Always "QRIS" for QRIS payments
                
        Note:
            - Generates random confirmation code for payment verification
            - Displays QR code in terminal for customer to scan
            - Allows up to 5 attempts for code confirmation
            - User can type 'x' to cancel payment at any time
        """
        code_to_qr = self.generateRandomString()  # Generate random confirmation code
        print("\n=== Scan QRIS di bawah ini untuk melakukan pembayaran ===")  # Payment header
        self.generateQrTerminal(code_to_qr)  # Display QR code in terminal
        print(
            "\nMasukkan kode konfirmasi yang Anda terima setelah melakukan pembayaran.\n"  # Instruction message
        )
        attempts = 5  # Maximum number of confirmation attempts
        for _ in range(1, attempts + 1):  # Loop through confirmation attempts
            code_from_user = inputWithTimeout(
                f"Masukkan kode konfirmasi ('x' untuk batal): "  # Confirmation prompt
            )
            if code_from_user.lower() == "x":  # Check for cancellation
                print("❌ - Membatalkan pembayaran QRIS.\n")  # Cancellation message
                return (False, "QRIS")
            if code_to_qr == code_from_user:  # Validate confirmation code
                print("\n✅ - Pembayaran berhasil.\n")  # Success message
                return (True, "QRIS")
            else:
                print("⚠ - Kode konfirmasi salah, silakan coba lagi.")  # Invalid code message
        print("⚠ - Kesempatan memasukkan kode telah habis.")  # Max attempts reached
        return (False, "QRIS")  # Return failure after max attempts

    def processPayment(self, total_price: int) -> Tuple[bool, Optional[str]]:
        """
        Handle payment process.
        
        Manages the overall payment workflow by presenting payment options,
        handling user selection, and delegating to appropriate payment methods
        (cash or QRIS). Validates input and provides error handling.
        
        Args:
            total_price (int): Total amount to be paid in Indonesian Rupiah
            
        Returns:
            Tuple[bool, Optional[str]]: (payment_success, payment_method)
                - payment_success: True if payment completed, False if cancelled/failed
                - payment_method: "Tunai" for cash, "QRIS" for QRIS, None if cancelled
                
        Note:
            - Displays payment menu and total amount
            - Supports cash (option 1) and QRIS (option 2) payments
            - User can type 'x' to cancel payment at any time
            - Validates input and handles invalid selections
        """
        print("\n\n*********** Pilih Metode Pembayaran ************")  # Payment menu header
        self.displayPaymentMethods()  # Show available payment options
        print(f">>> Total yang harus dibayar: Rp{total_price}")  # Display total amount
        while True:  # Loop until valid selection or cancellation
            payment_method_input = inputWithTimeout(
                "Pilih metode pembayaran ( 1 | 2 | 'x' untuk batal): "  # Payment method prompt
            )
            if payment_method_input.lower() == "x":  # Check for cancellation
                print("❌ - Membatalkan proses pembayaran.\n")  # Cancellation message
                return (False, None)
            try:
                payment_method = int(payment_method_input)  # Convert input to integer
                if payment_method == 1:  # Cash payment selected
                    return self.processCashPayment(total_price)
                elif payment_method == 2:  # QRIS payment selected
                    return self.processQrisPayment(total_price)
                else:
                    print(
                        "⚠ - Metode pembayaran tidak tersedia. Silakan pilih 1 atau 2."  # Invalid option message
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")  # Invalid input message


# ╒====================================╕
# |       QR SCANNER MANAGEMENT        |
# ╘====================================╛
class QrScanner:
    """Class to manage QR Code scanning process."""

    def __init__(self, db_manager: DatabaseManager, order_manager: OrderManager):
        """Initialize QR scanner with database manager and order manager."""
        self.db_manager = db_manager
        self.order_manager = order_manager
        self.coffee_list = order_manager.coffee_list
        self.menu_manager = order_manager.menu_manager

    def scanQr(self) -> None:
        """
        Scan QR code to confirm pending orders in the system.
        
        This method activates the camera to scan QR codes and processes them to confirm
        orders that have 'Pending' status in the database. The scanning continues until
        a valid QR code is detected or the user cancels the operation.
        
        Returns:
            None
            
        Notes:
            - Uses OpenCV for camera access and QR code detection
            - Displays real-time camera feed until QR code is found
            - Press 'q' to cancel scanning operation
            - Automatically releases camera resources after completion
            - Handles camera access errors gracefully
        """
        detector = cv2.QRCodeDetector()
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("\n⚠ - Tidak dapat membuka pemindai QR.\n\n")
            return
        print("\n\n*********** Pindai QR Code ************")
        print("Dekatkan QR Code ke alat pemindai QR")

        qr_code = ""
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠ - Tidak dapat membaca frame dari pemindai QR.\n\n")
                    break
                data, _, _ = detector.detectAndDecode(frame)
                if data:
                    qr_code = data
                    break
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("❌ - Pemindaian QR Code dibatalkan.\n\n")
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
        if not qr_code:
            print("⚠ - Tidak ada QR Code yang dipindai.\n\n")
            return

        qr_data = self.db_manager.queue_qr.get_all_records()
        queue_qr_columns = self.db_manager.getColumnIndices(
            self.db_manager.queue_qr
        )
        inventory_columns = self.db_manager.getColumnIndices(
            self.db_manager.inventory_sheet
        )
        self.coffee_list = self.db_manager.getCoffeeData()
        self.menu_manager.assignCoffeeNumbers()

        # Initialize order processing variables
        orders = []  # List to store valid orders from QR queue
        out_of_stock = False  # Flag to track if any items are out of stock
        valid = False  # Flag to track if QR code has been processed before
        
        # Process each row in QR queue data
        for index, row in enumerate(qr_data, start=2):  # Start from row 2 (skip header)
            # Check if QR matches and order is pending
            if str(row["QR"]) == qr_code and row["Status"] == "Pending":
                coffee_name = row["Jenis kopi"]  # Get coffee type from order
                ordered_quantity = int(row["Jumlah"])  # Get ordered quantity
                
                # Validate coffee availability in this machine
                if coffee_name not in self.coffee_list:
                    print(f"ℹ - Maaf, {coffee_name} tidak tersedia di mesin ini")
                    continue
                    
                coffee = self.coffee_list[coffee_name]  # Get coffee data
                current_stock = coffee.stock  # Get current stock level
                
                # Check if coffee is out of stock
                if current_stock <= 0:
                    out_of_stock = True
                    print(f"ℹ - Stok {coffee_name} habis, silahkan coba di mesin lain")
                    continue
                    
                # Determine processable quantity based on stock availability
                if current_stock < ordered_quantity:
                    print(
                        f"ℹ - Stok {coffee_name} tidak mencukupi. Tersisa {current_stock} cup."
                    )
                    processable_quantity = current_stock  # Process only available stock
                else:
                    processable_quantity = ordered_quantity  # Process full order

                # Create composition object from QR order data
                composition = Composition(
                    sugar=int(row.get("Gula", 0)),  # Sugar portions (default 0)
                    creamer=int(row.get("Krimer", 0)),  # Creamer portions (default 0)
                    milk=int(row.get("Susu", 0)),  # Milk portions (default 0)
                    chocolate=int(row.get("Cokelat", 0)),  # Chocolate portions (default 0)
                )
                temperature = row["Suhu"].lower()  # Get temperature preference

                # Add validated order to processing list
                self.order_manager.addOrder(
                    orders, coffee, temperature, composition, processable_quantity
                )

                # Update order status in QR queue spreadsheet
                if processable_quantity == ordered_quantity:
                    # Mark order as completed if fully processed
                    self.db_manager.queue_qr.update_cell(
                        index, queue_qr_columns["Status"], "Selesai"
                    )
                    self.db_manager.queue_qr.update_cell(
                        index, queue_qr_columns["Jumlah"], 0
                    )
                else:
                    # Update remaining quantity if partially processed
                    remaining_order = ordered_quantity - processable_quantity
                    self.db_manager.queue_qr.update_cell(
                        index, queue_qr_columns["Jumlah"], remaining_order
                    )

                # Update coffee stock in inventory spreadsheet
                new_stock = coffee.stock - processable_quantity  # Calculate new stock
                self.db_manager.inventory_sheet.update_cell(
                    coffee.row_number, inventory_columns["Sisa Persediaan"], new_stock
                )
                coffee.stock = new_stock  # Update local coffee object

            elif str(row["QR"]) == qr_code and row["Status"] == "Selesai":
                valid = True  # Mark QR as valid if found with completed status

        # Process completed orders or handle error cases
        if orders:
            print(" ")
            self.order_manager.orderSummary(orders)  # Display order summary
            print("\n☕ - Terima kasih! Silakan ambil kopi Anda.\n\n")
            # Record each order item as a sale transaction
            for item in orders:
                self.db_manager.recordSale(item, "Pembelian Daring Website")
        else:
            # Handle cases where no orders were processed
            if not out_of_stock:
                if valid:
                    print("ℹ - Semua pesanan dengan QR ini sudah selesai.\n\n")
                else:
                    print("⚠ - QR yang diberikan tidak valid.\n\n")


# ╒====================================╕
# |      COFFEE RESTOCK MANAGEMENT     |
# ╘====================================╛
class CoffeeRestock:
    """
    Manages coffee inventory restocking operations for the coffee machine.
    
    This class provides administrative functionality to restock coffee inventory
    when supplies run low. It includes admin authentication and interactive
    menu selection for restocking specific coffee types.
    
    Attributes:
        db_manager (DatabaseManager): Database interface for inventory updates
        menu_manager (MenuManager): Menu display and coffee list management
        coffee_list (Dict[str, CoffeeData]): Available coffee types and their data
    """

    def __init__(self, db_manager: DatabaseManager, menu_manager: MenuManager):
        """Initialize coffee restock with database manager and menu manager."""
        self.db_manager = db_manager
        self.menu_manager = menu_manager
        self.coffee_list = menu_manager.coffee_list

    def restockCoffee(self) -> None:
        """
        Administrative function to restock coffee inventory.
        
        This method provides a secure interface for authorized personnel to add
        stock to existing coffee types. It requires admin authentication and
        guides the user through the restocking process with input validation.
        
        Returns:
            None
            
        Notes:
            - Requires valid admin code for access (Config.admin_code)
            - Maximum 5 authentication attempts before lockout
            - Displays current coffee menu with stock levels
            - Validates restock quantities (positive integers only)
            - Updates both local data and Google Sheets database
            - Supports cancellation at any step with 'x' input
        """
        print("\n\n*********** Menu Restock Kopi ************")
        # Initialize admin authentication variables
        max_attempts = 5  # Maximum authentication attempts allowed
        attempts = 0  # Current attempt counter
        
        # Admin authentication loop with attempt limit
        while attempts < max_attempts:
            admin_code_input = inputWithTimeout(
                "Masukkan kode admin ('x' untuk batal): "
            )
            # Handle cancellation request
            if admin_code_input.lower() == "x":
                print("❌ - Membatalkan restock kopi.\n\n")
                return
                
            # Validate admin code input format
            try:
                admin_code = int(admin_code_input)  # Convert to integer
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")
                attempts += 1  # Increment failed attempt counter
                continue
                
            # Verify admin code against configuration
            if admin_code == Config.admin_code:
                # Main restocking loop (authenticated admin access)
                while True:
                    # Update and display current coffee menu with stock levels
                    self.menu_manager.assignCoffeeNumbers()  # Assign display numbers
                    self.menu_manager.displayCoffeeMenu()  # Show menu with current stock
                    
                    # Create mapping of menu numbers to coffee objects
                    coffee_name_by_number = {
                        coffee.number: coffee
                        for coffee in self.coffee_list.values()
                        if coffee.stock >= 0  # Include all coffees (even out of stock)
                    }
                    
                    # Coffee selection loop with input validation
                    while True:
                        coffee_choice_input = inputWithTimeout(
                            "Pilih kopi untuk restock ('x' untuk batal): "
                        )
                        # Handle cancellation request
                        if coffee_choice_input.lower() == "x":
                            print("❌ - Membatalkan restock kopi.\n\n")
                            return
                            
                        # Validate input is numeric
                        if not coffee_choice_input.isdigit():
                            print(
                                "⚠ - Input tidak valid. Silakan masukkan nomor kopi atau 'x' untuk batal."
                            )
                            continue
                            
                        # Validate coffee selection is within available options
                        coffee_choice = int(coffee_choice_input)
                        if coffee_choice not in coffee_name_by_number:
                            print(
                                "⚠ - Pilihan kopi tidak valid. Silakan pilih nomor yang tersedia."
                            )
                            continue
                            
                        coffee = coffee_name_by_number[coffee_choice]  # Get selected coffee
                        break  # Exit loop after selecting valid coffee

                    # Restock quantity input loop with validation
                    while True:
                        restock_quantity_input = inputWithTimeout(
                            "Masukkan jumlah restock ('x' untuk batal): "
                        )
                        # Handle cancellation request
                        if restock_quantity_input.lower() == "x":
                            print("❌ - Membatalkan restock kopi.\n\n")
                            return
                            
                        # Validate and process restock quantity
                        try:
                            restock_quantity = int(restock_quantity_input)  # Convert to integer
                            # Ensure positive quantity
                            if restock_quantity <= 0:
                                print("⚠ - Jumlah restock harus lebih dari 0.")
                                continue
                                
                            # Perform restock operation in database
                            self.db_manager.restockCoffee(coffee, restock_quantity)
                            print(
                                f"✅ - Berhasil restock {coffee.name} sebanyak {restock_quantity}. Stok baru: {coffee.stock}.\n\n"
                            )
                            break  # Exit loop after successful restock
                        except ValueError:
                            print("⚠ - Masukkan harus berupa angka.")

                    # Ask if user wants to continue restocking
                    while True:
                        again_input = inputWithTimeout(
                            "Apakah ingin melakukan restock lagi? ('y' untuk Ya | 'n' untuk Tidak): "
                        ).lower()
                        if again_input in ["y", "ya"]:
                            break  # Return to restock loop start
                        elif again_input in ["n", "tidak"]:
                            print("\n🔃 - Kembali ke menu utama.\n\n")
                            return
                        else:
                            print(
                                "⚠ - Input tidak valid. Silakan masukkan 'y' atau 'n'."
                            )
                    return  # Exit after user chooses not to continue
            else:
                # Handle incorrect admin code
                attempts += 1  # Increment failed attempt counter
                print("⚠ - Kode admin salah! Coba lagi.")
                
        # Handle maximum authentication attempts exceeded
        print("⚠ - Autentikasi administrator gagal.")


# ╒====================================╕
# |   MAIN: COFFEE MACHINE HANDLER     |
# ╘====================================╛
class CoffeeMachine:
    """
    Main controller class for the coffee machine system.
    
    This class orchestrates all coffee machine operations including order management,
    payment processing, QR code scanning, inventory restocking, and system administration.
    It serves as the central hub that coordinates between all subsystem components.
    
    Attributes:
        db_manager (DatabaseManager): Handles database operations and Google Sheets integration
        coffee_list (Dict[str, CoffeeData]): Available coffee types and their current data
        menu_manager (MenuManager): Manages coffee menu display and numbering
        order_manager (OrderManager): Handles customer order processing and customization
        payment_manager (PaymentManager): Processes cash and QRIS payments
        qr_scanner_manager (QrScanner): Manages QR code scanning for order confirmation
        restock_manager (CoffeeRestock): Handles administrative inventory restocking
    """

    def __init__(self):
        """Initialize coffee machine and load initial data."""
        self.db_manager: DatabaseManager = DatabaseManager()
        self.coffee_list: Dict[str, CoffeeData] = self.db_manager.getCoffeeData()
        self.menu_manager: MenuManager = MenuManager(self.coffee_list)
        self.order_manager: OrderManager = OrderManager(self.coffee_list, self.menu_manager)
        self.payment_manager: PaymentManager = PaymentManager()
        self.qr_scanner_manager: QrScanner = QrScanner(self.db_manager, self.order_manager)
        self.restock_manager: CoffeeRestock = CoffeeRestock(self.db_manager, self.menu_manager)
        self.menu_manager.assignCoffeeNumbers()

    def shutdownProgram(self):
        """
        Securely shutdown the coffee machine system with admin authentication.
        
        This method provides a secure way to terminate the coffee machine program.
        It requires admin authentication to prevent unauthorized shutdowns and
        includes multiple attempt validation for security.
        
        Returns:
            None
            
        Notes:
            - Requires valid admin code for access (Config.admin_code)
            - Maximum 5 authentication attempts before denial
            - Exits the entire program upon successful authentication
            - Supports cancellation with 'x' input
            - Displays appropriate feedback for invalid attempts
        """
        print("\n\n*********** Menonaktifkan Program ************")
        # Initialize admin authentication variables
        max_attempts = 5  # Maximum authentication attempts allowed
        attempts = 0  # Current attempt counter
        
        # Admin authentication loop with attempt limit
        while attempts < max_attempts:
            admin_code_input = inputWithTimeout(
                "Masukkan kode admin ('x' untuk batal): "
            )
            # Handle cancellation request
            if admin_code_input.lower() == "x":
                print("❌ - Membatalkan penonaktifan program.\n\n")
                return
                
            # Validate admin code input format
            try:
                admin_code = int(admin_code_input)  # Convert to integer
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")
                attempts += 1  # Increment failed attempt counter
                continue

            # Verify admin code and shutdown if correct
            if admin_code == Config.admin_code:
                print("💤 - Algoritma dimatikan. Program akan keluar.")
                sys.exit(0)  # Exit the entire program
            else:
                # Handle incorrect admin code
                attempts += 1  # Increment failed attempt counter
                print(
                    f"⚠ - Kode admin salah! {max_attempts - attempts} percobaan tersisa."
                )
                
        # Handle maximum authentication attempts exceeded
        print("⚠ - Autentikasi administrator gagal. Kembali ke menu utama.")

    def coffeeMachineSimulation(self) -> None:
        """
        Main simulation loop for the virtual coffee machine system.
        
        This method provides the primary user interface and orchestrates all coffee machine
        operations through an interactive menu system. It continuously runs until the user
        chooses to shutdown the system or exits the program.
        
        Menu Options:
            1. Mulai Pemesanan - Start coffee ordering process
            2. Scan QR - Scan QR codes for order confirmation
            3. Restock Kopi (Admin) - Administrative inventory restocking
            4. Shutdown Program (Admin) - Secure system shutdown
        
        Returns:
            None
            
        Notes:
            - Runs in an infinite loop until explicit termination
            - Validates stock availability before processing orders
            - Handles payment processing and order completion
            - Provides appropriate feedback for all user actions
            - Gracefully handles invalid menu selections
            - Updates inventory and records sales automatically
        """
        # Display welcome message
        print("\n=== Selamat datang di Mesin Kopi Virtual! ===\n")
        
        # Main program loop - runs until shutdown
        while True:
            # Display main menu options
            print("======= Pilihan Menu =======")
            print("1. Mulai Pemesanan")  # Start coffee ordering process
            print("2. Scan QR")  # QR code scanning for order confirmation
            print("3. Restock Kopi (Admin)")  # Administrative inventory restocking
            print("4. Shutdown Program (Admin)")  # Secure system shutdown
            print("============================")
            
            # Get user menu selection
            choice = input("Pilih opsi (1, 2, 3, 4): ")
            
            # Handle coffee ordering process (Option 1)
            if choice == "1":
                # Check if any coffee is available
                if not self.coffee_list:
                    print(
                        "\n💔 - Maaf, semua kopi telah habis. Silakan kembali lain waktu.\n\n"
                    )
                    continue
                    
                # Start coffee selection process
                orders = self.order_manager.selectCoffee()
                
                # Process orders if any were created
                if orders:
                    # Validate stock sufficiency for all ordered items
                    stock_sufficient = True
                    for item in orders:
                        if item.coffee.stock < item.quantity:
                            print(
                                f"☕ - Stok {item.coffee.name} tidak mencukupi. Tersisa {item.coffee.stock}."
                            )
                            stock_sufficient = False
                            
                    # Return to menu if insufficient stock
                    if not stock_sufficient:
                        print(
                            "🔃 - Silakan ulangi pemesanan dengan jumlah yang tersedia.\n\n"
                        )
                        continue
                        
                    # Display order summary and process payment
                    print(" \n ")
                    total_price = self.order_manager.orderSummary(orders)  # Calculate total
                    (
                        payment_success,
                        method,
                    ) = self.payment_manager.processPayment(total_price)  # Process payment
                    
                    # Handle successful payment
                    if payment_success:
                        print("☕ - Terima kasih! Silakan ambil kopi Anda.\n\n")
                        # Record sales and update inventory for each item
                        for item in orders:
                            self.db_manager.recordSale(item, method)  # Record transaction
                            self.db_manager.updateStock(item.coffee, item.quantity)  # Update stock
                        # Refresh coffee data and menu numbers
                        self.coffee_list = self.db_manager.getCoffeeData()
                        self.menu_manager.assignCoffeeNumbers()
                    else:
                        # Handle payment failure or cancellation
                        if method is None:
                            print(
                                "💰 - Pembayaran dibatalkan. Kembali ke menu utama.\n\n"
                            )
                        else:
                            print("📉 - Pembayaran gagal. Kembali ke menu utama.\n\n")
                else:
                    # Handle order cancellation or no orders
                    print(
                        "📃 - Pemesanan dibatalkan atau tidak ada pesanan. Kembali ke menu utama.\n\n"
                    )
            # Handle QR code scanning (Option 2)
            elif choice == "2":
                self.qr_scanner_manager.scanQr()  # Start QR scanning process
                
            # Handle coffee restocking (Option 3 - Admin only)
            elif choice == "3":
                self.restock_manager.restockCoffee()  # Admin restock process
                # Refresh coffee data and menu numbers after restocking
                self.coffee_list = self.db_manager.getCoffeeData()
                self.menu_manager.assignCoffeeNumbers()
                
            # Handle program shutdown (Option 4 - Admin only)
            elif choice == "4":
                self.shutdownProgram()  # Secure admin shutdown
                
            # Handle invalid menu selection
            else:
                print("⚠ - Pilihan tidak valid. Silakan pilih 1, 2, 3, atau 4")


# ╒====================================╕
# |         RUN PROGRAM                |
# ╘====================================╛

# Program entry point - executes only when script is run directly
if __name__ == "__main__":
    # Initialize the coffee machine system
    coffee_machine = CoffeeMachine()
    
    # Start the main coffee machine simulation
    coffee_machine.coffeeMachineSimulation()