"""
This file is responsible for managing all interactions with Google Sheets,
acting as a database abstraction layer for the coffee machine application.

Key functionalities of `DatabaseManager` include:
- Initializing the connection to Google Sheets using secure credentials.
- Loading initial data from various worksheets (coffee inventory, additives, etc.)
  into a local cache for fast access and to reduce API calls.
- Providing a queue mechanism to handle write operations (like stock updates
  and sales logging) asynchronously.
- Running a periodic synchronization thread to push updates from the queue
  to Google Sheets, ensuring data consistency.
- Managing synchronous operations (e.g., restocking) that require immediate updates.
- Handling the storage and retrieval of the admin code.
"""

from typing import Dict, List

import threading
import time
import queue
import os

import gspread
from google.oauth2.service_account import Credentials

from apps.data_classes import CoffeeData, QRCodeData, SalesRecord
from credentials.config import Configuration

class DatabaseManager:
    """
    Manages the connection, caching, and data synchronization with Google Sheets.

    This class uses a thread for periodic data synchronization, minimizing latency
    and API calls. All write operations are queued and processed in batches.

    Attributes:
        coffee_stock_ws (gspread.Worksheet): Worksheet for coffee stock.
        additives_ws (gspread.Worksheet): Worksheet for additive stock.
        qr_code_ws (gspread.Worksheet): Worksheet for QR payment data.
        sales_ws (gspread.Worksheet): Worksheet for sales history.
        online_orders_ws (gspread.Worksheet): Worksheet for QR order queue.
        lock (threading.Lock): Lock for thread-safe access to the cache.
        update_queue (queue.Queue): Queue for asynchronous write operations.
        coffee_list (Dict[str, CoffeeData]): Cache for coffee data.
        additives_list (Dict[str, int]): Cache for additive data.
        qr_code_list (List[QRCodeData]): Cache for QR reference data.
        admin_code (int): Admin code loaded from a file.
    """

    def __init__(self):
        """
        Initializes the DatabaseManager.
        
        - Sets up the connection to Google Sheets.
        - Loads initial data into the local cache.
        - Starts a thread for periodic synchronization.
        """
        # Set up credentials and authorize with Google Sheets
        credentials = Credentials.from_service_account_file(
            Configuration.SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(Configuration.SHEET_ID)

        # Initialize worksheets to be used
        self.coffee_stock_ws = spreadsheet.worksheet("PersediaanKopi")
        self.additives_ws = spreadsheet.worksheet("PersediaanTambahan")
        self.qr_code_ws = spreadsheet.worksheet("ReferenceID")
        self.sales_ws = spreadsheet.worksheet("DataPenjualan")
        self.online_orders_ws = spreadsheet.worksheet("AntrianPesananQR")

        # Initialize lock, queue, and local data cache
        self.lock = threading.Lock()
        self.update_queue = queue.Queue()

        # Load initial data from Google Sheets into cache
        self.coffee_list = self.load_coffee_data()
        self.additives_list = self.load_additive_data()
        self.qr_code_list = self.load_qr_code_list()

        # Load admin code from a local file
        self.admin_code = self.load_admin_code()

        # Start the periodic synchronization thread in the background
        self.sync_thread = threading.Thread(
            target=self.periodic_sync, daemon=True
        )
        self.sync_thread.start()

    def get_column_indices(self, worksheet: gspread.Worksheet) -> Dict[str, int]:
        """
        Gets the mapping of column names to column indices (1-based) from a worksheet.

        Args:
            worksheet (gspread.Worksheet): The worksheet to read the header from.

        Returns:
            Dict[str, int]: A dictionary mapping column names to their index numbers.
        """
        header = worksheet.row_values(1)
        return {name: idx + 1 for idx, name in enumerate(header)}

    def load_admin_code(self) -> int:
        """
        Loads the admin code from the `admin_code.txt` file.
        If the file does not exist or is corrupted, it creates a new file with the default code.

        Returns:
            int: The admin code to be used.
        """
        admin_file = os.path.join(os.getcwd(), "credentials", "admin_code.txt")
        if os.path.exists(admin_file):
            with open(admin_file, "r") as f:
                code = f.read().strip()
                try:
                    return int(code)
                except ValueError:
                    # If the file is corrupted or its content is invalid, use the default code
                    return Configuration.DEFAULT_ADMIN_CODE
        else:
            # If the file does not exist, create it with the default code
            with open(admin_file, "w") as f:
                f.write(str(Configuration.DEFAULT_ADMIN_CODE))
            return Configuration.DEFAULT_ADMIN_CODE

    def save_admin_code(self, new_code: int) -> None:
        """
        Saves the new admin code to the `admin_code.txt` file permanently.

        Args:
            new_code (int): The new admin code to be saved.
        """
        admin_file = os.path.join(os.getcwd(), "credentials", "admin_code.txt")
        with open(admin_file, "w") as f:
            f.write(str(new_code))
        self.admin_code = new_code

    def load_coffee_data(self) -> Dict[str, CoffeeData]:
        """
        Loads coffee inventory data from the 'PersediaanKopi' worksheet into the local cache.

        Returns:
            Dict[str, CoffeeData]: A dictionary of coffee data with coffee names as keys.
        """
        coffee_data = self.coffee_stock_ws.get_all_records()
        with self.lock:
            return {
                row["Jenis Kopi"]: CoffeeData(
                    name=row["Jenis Kopi"],
                    price=int(row["Harga"]),
                    stock=int(row["Sisa Persediaan"]),
                    row_number=i + 2,  # Data rows start after the header (row 1)
                )
                for i, row in enumerate(coffee_data)
            }

    def load_additive_data(self) -> Dict[str, int]:
        """
        Loads additive inventory data from the 'PersediaanTambahan' worksheet.

        Returns:
            Dict[str, int]: A dictionary of additive data with additive names as keys.
        """
        additive_data = self.additives_ws.get_all_records()
        with self.lock:
            return {
                row["Jenis Bahan Tambahan"]: int(row["Sisa Persediaan"])
                for row in additive_data
            }

    def load_qr_code_list(self) -> List[QRCodeData]:
        """
        Loads QR payment reference data from the 'ReferenceID' worksheet into the local cache.

        Returns:
            List[QRCodeData]: A list of `QRCodeData` objects.
        """
        records = self.qr_code_ws.get_all_records()
        with self.lock:
            qr_list = []
            for i, record in enumerate(records):
                qr_list.append(
                    QRCodeData(
                        ref_id=record["Reference ID"],
                        total_price=int(record["Total Harga"]),
                        payment_method=record["Metode"],
                        timestamp=record["Timestamp"],
                        status=record["Status"],
                        row_number=i + 2,
                    )
                )
            return qr_list

    def get_bestselling_coffee(self) -> str:
        """
        Analyzes sales data to find the most sold coffee.

        Returns:
            str: The name of the bestselling coffee. Returns an empty string if there is no sales data.
        """
        sales_data = self.sales_ws.get_all_records()
        counts = {}
        for row in sales_data:
            name = row.get("jenis_kopi")
            if not name:
                continue
            
            if name not in counts:
                counts[name] = 0
            
            # Extract quantity from 'x{number}' format
            quantity_str = row.get("Jumlah", "").replace("x", "")
            try:
                quantity_int = int(quantity_str)
            except (ValueError, TypeError):
                quantity_int = 0
            
            counts[name] += quantity_int

        if not counts:
            return ""
        
        # Find the coffee with the highest sales
        bestseller = max(counts, key=counts.get)
        return bestseller

    def periodic_sync(self) -> None:
        """
        Runs an infinite loop for periodic data synchronization.
        
        This method processes all items in the `update_queue` and then
        pushes data changes (stock, QR status) to Google Sheets.
        """
        while True:
            try:
                # Process all operations in the queue until it's empty
                while not self.update_queue.empty():
                    operation = self.update_queue.get_nowait()
                    op_type = operation[0]
                    
                    if op_type == "update_stock":
                        _, coffee_name, quantity_sold = operation
                        self.update_stock(coffee_name, quantity_sold)
                    elif op_type == "restock_coffee":
                        _, coffee_name, restock_quantity = operation
                        self.restock_coffee(coffee_name, restock_quantity)
                    elif op_type == "update_qr_status":
                        _, ref_id, new_status = operation
                        self.update_qr_status(ref_id, new_status)
                    elif op_type == "log_sale":
                        _, sales_record = operation
                        self.log_sale(sales_record)
                    elif op_type == "update_additive":
                        _, additive, quantity = operation
                        self.update_additive(additive, quantity)

                # Synchronize coffee data to Google Sheets
                with self.lock:
                    for coffee in self.coffee_list.values():
                        self.coffee_stock_ws.update_cell(
                            coffee.row_number, 3, coffee.stock
                        )

                # Synchronize additive data
                additive_data = self.additives_ws.get_all_records()
                additive_row_map = {
                    row["Jenis Bahan Tambahan"]: idx + 2
                    for idx, row in enumerate(additive_data)
                }
                for additive, stock in self.additives_list.items():
                    row_number = additive_row_map.get(additive)
                    if row_number:
                        self.additives_ws.update_cell(row_number, 2, stock)

                # Synchronize QR status
                for qr in self.qr_code_list:
                    self.qr_code_ws.update_cell(qr.row_number, 5, qr.status)

                time.sleep(Configuration.SYNC_INTERVAL)

            except Exception as e:
                print(f"⚠ - Terjadi kesalahan saat sinkronisasi periodik:\n{e}")
                time.sleep(Configuration.SYNC_INTERVAL)

    def enqueue_update_stock(self, coffee_name: str, quantity_sold: int) -> None:
        """
        Adds a coffee stock reduction operation to the queue.

        Args:
            coffee_name (str): The name of the coffee whose stock will be reduced.
            quantity_sold (int): The amount of stock to be reduced.
        """
        self.update_queue.put(("update_stock", coffee_name, quantity_sold))

    def enqueue_restock_coffee(self, coffee_name: str, restock_quantity: int) -> None:
        """
        Adds a coffee stock increase (restock) operation to the queue.

        Args:
            coffee_name (str): The name of the coffee to be restocked.
            restock_quantity (int): The amount of stock to be added.
        """
        self.update_queue.put(("restock_coffee", coffee_name, restock_quantity))

    def enqueue_update_qr_status(self, ref_id: str, new_status: str) -> None:
        """
        Adds a QR payment status update operation to the queue.

        Args:
            ref_id (str): The reference ID of the QR transaction.
            new_status (str): The new status ('Selesai', 'Expired').
        """
        self.update_queue.put(("update_qr_status", ref_id, new_status))

    def enqueue_log_sale(self, sales_record: SalesRecord) -> None:
        """
        Adds a new sales data logging operation to the queue.

        Args:
            sales_record (SalesRecord): The sales data object to be logged.
        """
        self.update_queue.put(("log_sale", sales_record))

    def enqueue_update_additive(self, additive: str, quantity: int) -> None:
        """
        Adds an additive stock update operation to the queue.

        Args:
            additive (str): The name of the additive to be updated.
            quantity (int): The amount to be added (positive) or reduced (negative).
        """
        self.update_queue.put(("update_additive", additive, quantity))

    def update_stock(self, coffee_name: str, quantity_sold: int) -> None:
        """
        Updates the coffee stock in the local cache. This is an internal operation.

        Args:
            coffee_name (str): The name of the coffee whose stock is being updated.
            quantity_sold (int): The quantity sold (to be subtracted from the stock).
        """
        if coffee_name in self.coffee_list:
            coffee = self.coffee_list[coffee_name]
            coffee.stock = max(0, coffee.stock - quantity_sold)

    def restock_coffee(self, coffee_name: str, restock_quantity: int) -> None:
        """
        Increases the coffee stock in the local cache. This is an internal operation.

        Args:
            coffee_name (str): The name of the restocked coffee.
            restock_quantity (int): The amount of stock added.
        """
        if coffee_name in self.coffee_list:
            coffee = self.coffee_list[coffee_name]
            coffee.stock += restock_quantity

    def update_qr_status(self, ref_id: str, new_status: str) -> None:
        """
        Updates the QR payment status in the local cache. This is an internal operation.

        Args:
            ref_id (str): The reference ID of the QR transaction.
            new_status (str): The new status for the transaction.
        """
        for qr in self.qr_code_list:
            if qr.ref_id == ref_id:
                qr.status = new_status
                break

    def log_sale(self, sales_record: SalesRecord) -> None:
        """
        Logs new sales data to the 'DataPenjualan' worksheet.

        Args:
            sales_record (SalesRecord): The sales data object.
        """
        self.sales_ws.append_row(
            [
                sales_record.coffee_type,
                sales_record.temperature,
                sales_record.composition,
                sales_record.quantity,
                sales_record.total_price,
                sales_record.payment_method,
            ]
        )

    def update_additive(self, additive: str, quantity: int) -> None:
        """
        Updates the additive stock in the local cache. This is an internal operation.

        Args:
            additive (str): The name of the updated additive.
            quantity (int): The amount to be added or subtracted.
        """
        if additive in self.additives_list:
            self.additives_list[additive] = max(0, self.additives_list[additive] + quantity)

    def save_changes_before_exit(self) -> None:
        """
        Forces synchronization of all pending changes before the program exits.
        
        This method empties the update queue and sends all changes
        directly to Google Sheets.
        """
        try:
            # Process all remaining items in the queue
            while not self.update_queue.empty():
                operation = self.update_queue.get_nowait()
                op_type = operation[0]
                if op_type == "update_stock":
                    _, coffee_name, quantity_sold = operation
                    self.update_stock(coffee_name, quantity_sold)
                elif op_type == "restock_coffee":
                    _, coffee_name, restock_quantity = operation
                    self.restock_coffee(coffee_name, restock_quantity)
                elif op_type == "update_qr_status":
                    _, ref_id, new_status = operation
                    self.update_qr_status(ref_id, new_status)
                elif op_type == "log_sale":
                    _, sales_record = operation
                    self.log_sale(sales_record)
                elif op_type == "update_additive":
                    _, additive, quantity = operation
                    self.update_additive(additive, quantity)

            # Perform a final update to Google Sheets for all data
            with self.lock:
                # Update coffee stock
                for coffee in self.coffee_list.values():
                    self.coffee_stock_ws.update_cell(
                        coffee.row_number, 3, coffee.stock
                    )

                # Update additive stock
                additive_data = self.additives_ws.get_all_records()
                additive_row_map = {
                    row["Jenis Bahan Tambahan"]: idx + 2
                    for idx, row in enumerate(additive_data)
                }
                for additive, stock in self.additives_list.items():
                    row_number = additive_row_map.get(additive)
                    if row_number:
                        self.additives_ws.update_cell(row_number, 2, stock)

                # Update QR status
                for qr in self.qr_code_list:
                    self.qr_code_ws.update_cell(qr.row_number, 5, qr.status)

        except Exception as e:
            print(f"⚠ - Terjadi kesalahan saat menyimpan perubahan terakhir:\n{e}")
            time.sleep(Configuration.SYNC_INTERVAL) # Pause if an error occurs

    def restock_coffee_sync(self, coffee_name: str, restock_quantity: int) -> None:
        """
        Performs a synchronous coffee restock (directly to Google Sheets).

        Args:
            coffee_name (str): The name of the coffee to be restocked.
            restock_quantity (int): The amount of stock to be added.
        """
        with self.lock:
            if coffee_name in self.coffee_list:
                coffee = self.coffee_list[coffee_name]
                coffee.stock += restock_quantity
                # Directly update Google Sheets
                self.coffee_stock_ws.update_cell(coffee.row_number, 3, coffee.stock)

    def restock_additives_sync(self, additive: str, restock_quantity: int) -> None:
        """
        Performs a synchronous additive restock (directly to Google Sheets).

        Args:
            additive (str): The name of the additive to be restocked.
            restock_quantity (int): The amount of stock to be added.
        """
        with self.lock:
            if additive in self.additives_list:
                self.additives_list[additive] += restock_quantity
                # Directly update Google Sheets
                records = self.additives_ws.get_all_records()
                additive_row_map = {
                    row["Jenis Bahan Tambahan"]: idx + 2
                    for idx, row in enumerate(records)
                }
                row_number = additive_row_map.get(additive)
                if row_number:
                    self.additives_ws.update_cell(
                        row_number, 2, self.additives_list[additive]
                    )
