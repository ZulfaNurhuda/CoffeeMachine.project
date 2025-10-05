"""
This file defines the `OnlineOrderManager` class, which is responsible for
handling orders initiated by scanning a QR code. This typically involves orders
placed through a separate web interface.

Key functionalities include:
- Using the camera to scan and decode a QR code.
- Fetching the corresponding order details from the 'AntrianPesananQR' worksheet
  in Google Sheets based on the scanned QR code.
- Validating the order against the current machine's inventory (both coffee and additives).
- Processing the order if the stock is sufficient, or partially processing if stock is limited.
- Updating the order status and remaining quantities in Google Sheets.
- Updating the local stock cache and logging the sale.
"""

import cv2

from apps.database.database_manager import DatabaseManager
from apps.managers.order_manager import OrderManager
from apps.data_classes import CompositionData, SalesRecord

class OnlineOrderManager:
    """Manages the processing of scanning QR codes for online order queues."""

    def __init__(self, db_manager: DatabaseManager, order_manager: OrderManager):
        """
        Initializes the OnlineOrderManager.

        Args:
            db_manager (DatabaseManager): The database manager for data interaction.
            order_manager (OrderManager): The order manager to handle order processing.
        """
        self.db_manager = db_manager
        self.order_manager = order_manager
        self.coffee_list = order_manager.coffee_list
        self.menu_manager = order_manager.menu_manager

    def format_composition(self, composition: CompositionData) -> str:
        """
        Formats a CompositionData object into a string for storage in Google Sheets.

        Args:
            composition (CompositionData): The composition object to be formatted.

        Returns:
            str: A string representation of the composition.
        """
        parts = []
        if composition.sugar > 0:
            parts.append(f"Gula: {composition.sugar}")
        if composition.creamer > 0:
            parts.append(f"Krimer: {composition.creamer}")
        if composition.milk > 0:
            parts.append(f"Susu: {composition.milk}")
        if composition.chocolate > 0:
            parts.append(f"Cokelat: {composition.chocolate}")
        return ", ".join(parts) if parts else "Tanpa tambahan"

    def scan_qr(self) -> None:
        """Scans a QR code and confirms orders with a `Pending` status."""
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

        qr_data = self.db_manager.online_orders_ws.get_all_records()
        online_order_col_indices = self.db_manager.get_column_indices(
            self.db_manager.online_orders_ws
        )
        inventory_col_indices = self.db_manager.get_column_indices(
            self.db_manager.coffee_stock_ws
        )
        self.coffee_list = self.db_manager.coffee_list
        self.menu_manager.set_coffee_numbers()

        order = []
        out_of_stock = False
        is_valid = False
        for index, row in enumerate(qr_data, start=2):
            if str(row["QR"]) == qr_code and row["Status"] == "Pending":
                coffee_name = row["Jenis kopi"]
                ordered_quantity = int(row["Jumlah"])
                if coffee_name not in self.coffee_list:
                    print(f"ℹ - Maaf, {coffee_name} tidak tersedia di mesin ini")
                    continue
                coffee = self.coffee_list[coffee_name]
                current_stock = coffee.stock
                if current_stock <= 0:
                    out_of_stock = True
                    print(f"ℹ - Stok {coffee_name} habis, silahkan coba di mesin lain")
                    continue
                if current_stock < ordered_quantity:
                    print(
                        f"ℹ - Stok {coffee_name} tidak mencukupi. Tersisa {current_stock} cup."
                    )
                    processable_quantity = current_stock
                else:
                    processable_quantity = ordered_quantity

                composition = CompositionData(
                    sugar=int(row.get("Gula", 0)),
                    creamer=int(row.get("Krimer", 0)),
                    milk=int(row.get("Susu", 0)),
                    chocolate=int(row.get("Cokelat", 0)),
                )
                temperature = row["Suhu"].lower()

                # Add the order to the list
                self.order_manager.add_to_order(
                    order, coffee, temperature, composition, processable_quantity
                )

                # Update the order status in Google Sheets
                if processable_quantity == ordered_quantity:
                    self.db_manager.online_orders_ws.update_cell(
                        index, online_order_col_indices["Status"], "Selesai"
                    )
                    self.db_manager.online_orders_ws.update_cell(
                        index, online_order_col_indices["Jumlah"], 0
                    )
                else:
                    remaining_order = ordered_quantity - processable_quantity
                    self.db_manager.online_orders_ws.update_cell(
                        index, online_order_col_indices["Jumlah"], remaining_order
                    )

                new_stock = coffee.stock - processable_quantity
                self.db_manager.coffee_stock_ws.update_cell(
                    coffee.row_number,
                    inventory_col_indices["Sisa Persediaan"],
                    new_stock,
                )
                coffee.stock = new_stock

            elif str(row["QR"]) == qr_code and row["Status"] == "Selesai":
                is_valid = True

        if order:
            print(" ")
            self.order_manager.summarize_order(order)
            print("\n☕ - Terima kasih! Silakan ambil kopi Anda.\n\n")
            for item in order:
                # Format the composition before logging the sale
                composition_str = self.format_composition(item.composition)
                self.db_manager.log_sale(
                    SalesRecord(
                        coffee_type=item.coffee.name,
                        temperature=item.temperature,
                        composition=composition_str,  # Use the formatted string
                        quantity=f"x{item.quantity}",
                        total_price=item.coffee.price,
                        payment_method="Pembelian Daring Melalui Website",
                    )
                )
        else:
            if not out_of_stock:
                if is_valid:
                    print("ℹ - Semua pesanan dengan QR ini sudah selesai.\n\n")
                else:
                    print("⚠ - QR yang diberikan tidak valid.\n\n")
