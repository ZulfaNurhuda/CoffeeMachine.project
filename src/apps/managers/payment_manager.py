"""
This file defines the `PaymentManager` class, which is responsible for handling
all payment-related processes in the coffee machine application.

This class manages different payment methods, including:
- **Cash Payments**: It guides the user through the process of inserting cash,
  calculating the total paid, and providing change.
- **QRIS Payments**: It generates a unique QR code for each transaction,
  displays it to the user, and then polls the database to check for payment
  confirmation from the web service. It also handles payment timeouts.

The manager interacts with the `DatabaseManager` to record transaction details
and update payment statuses.
"""

from typing import Tuple, Optional
import socket
import time
import random
import string
from datetime import datetime

import qrcode
import qrcode.constants

from apps.database.database_manager import DatabaseManager
from apps.data_classes import QRCodeData
from apps.utils.input_utils import input_with_timeout
from credentials.config import Configuration

class PaymentManager:
    """Manages the payment process."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the PaymentManager with a DatabaseManager instance.

        Args:
            db_manager (DatabaseManager): The DatabaseManager object to interact with the database.
        """
        self.db_manager = db_manager

    def display_payment_methods(self) -> None:
        """
        Displays the available payment methods to the user.
        """
        print("=== Metode Pembayaran Tersedia ===")
        print("1. Tunai")
        print("2. QRIS")
        print("==================================")

    def process_cash_payment(self, total_price: int) -> Tuple[bool, str]:
        """
        Handles the cash payment process.

        It repeatedly asks the user to insert money until the total amount is paid.
        It calculates and displays the change.

        Args:
            total_price (int): The total price to be paid.

        Returns:
            Tuple[bool, str]: A tuple containing the payment status (bool) and the payment method (str).
        """
        total_paid = 0
        while total_paid < total_price:
            money_input = input_with_timeout(
                self.db_manager, f"Masukkan uang pembayaran ('x' untuk batal): Rp"
            )
            if money_input.lower() == "x":
                print("❌ - Membatalkan pembayaran tunai.\n")
                return False, "Tunai"
            try:
                amount = int(money_input)
                if amount <= 0:
                    print(
                        "⚠ - Jumlah uang harus lebih besar dari Rp0. Silakan masukkan kembali."
                    )
                    continue
                total_paid += amount
                if total_paid >= total_price:
                    change = total_paid - total_price
                    print(
                        f"\n✅ - Pembayaran berhasil. Kembalian Anda: Rp{change}\n"
                    )
                    return True, "Tunai"
                else:
                    shortage = total_price - total_paid
                    print(
                        f"ℹ - Uang kurang. Anda masih kurang Rp{shortage}. Silakan masukkan kembali."
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")
        return False, "Tunai"

    def generate_random_string(self, length: int = 10) -> str:
        """
        Generates a random string of a specified length.

        Args:
            length (int): The desired length of the string (default: 10).

        Returns:
            str: A random string of the specified length.
        """
        return "".join(random.choices(string.digits, k=length))

    def generate_qr(self, data: str) -> None:
        """
        Creates a QR code and displays it in ASCII format in the terminal.

        Args:
            data (str): The data to be encoded into the QR code.
        """
        qr = qrcode.QRCode(
            version=1,  # QR Code size
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        qr.print_ascii()

    def process_qris_payment(self, total_price: int) -> Tuple[bool, str]:
        """
        Handles QRIS payment by printing a QR code in the terminal.

        This method generates a unique reference ID, creates a URL for the web service,
        displays it as a QR code, and polls for payment status updates.

        Args:
            total_price (int): The total price to be paid.

        Returns:
            Tuple[bool, str]: A tuple containing the payment status (bool) and the payment method (str).
        """
        print(
            f"\n🔃 - Memproses pembayaran QRIS untuk Rp{total_price}, mohon tunggu sebentar!"
        )

        # Generate a unique Reference ID
        ref_id = self.generate_random_string()
        local_ip = socket.gethostbyname(socket.gethostname())
        qr_data_url = f"http://{local_ip}:{Configuration.PORT}/search?ref_id={ref_id}"

        # Create the QR code
        self.generate_qr(qr_data_url)

        # Add QR data to the worksheet
        self.db_manager.qr_code_ws.append_row(
            [
                ref_id,
                total_price,
                "Pembayaran QRIS",
                datetime.now().strftime("%d-%m-%Y, %H:%M:%S"),
                "Pending",
            ]
        )
        # Add QR data to the local cache
        with self.db_manager.lock:
            self.db_manager.qr_code_list.append(
                QRCodeData(
                    ref_id=ref_id,
                    total_price=total_price,
                    payment_method="Pembayaran QRIS",
                    timestamp=datetime.now().strftime("%d-%m-%Y, %H:%M:%S"),
                    status="Pending",
                    row_number=len(self.db_manager.qr_code_list) + 2,
                )
            )

        # Wait for payment to complete or timeout
        start_time = time.time()
        while True:
            time.sleep(5)  # Wait 5 seconds before checking status

            # Check if the time has exceeded the timeout
            if time.time() - start_time > Configuration.QRIS_TIMEOUT:
                self.db_manager.enqueue_update_qr_status(ref_id, "Expired")
                print("⚠ - Pembayaran QRIS telah kadaluarsa.\n")
                return False, "QRIS"

            # Check QR status from the database
            status = self.check_qr_status(ref_id)
            if status == "Selesai":
                print("✅ - Pembayaran QRIS berhasil.\n")
                return True, "QRIS"
            elif status == "Expired":
                print("⚠ - Pembayaran QRIS kadaluarsa.\n")
                return False, "QRIS"

    def check_qr_status(self, ref_id: str) -> str:
        """
        Checks the status of a QR code from the local cache.

        Args:
            ref_id (str): The reference ID of the QR to check.

        Returns:
            str: The status of the QR code.
        """
        with self.db_manager.lock:
            for data in self.db_manager.qr_code_list:
                if data.ref_id == ref_id:
                    return data.status
        return "Pending"

    def process_payment(self, total_price: int) -> Tuple[bool, Optional[str]]:
        """
        Handles the overall payment process.

        Args:
            total_price (int): The total price to be paid.

        Returns:
            Tuple[bool, Optional[str]]: A tuple containing the payment status (bool) and the payment method (str) if successful, or None if canceled.
        """
        print("\n*********** Pilih Metode Pembayaran ************")
        self.display_payment_methods()
        print(f">>> Total yang harus dibayar: Rp{total_price}")
        while True:
            payment_method_input = input_with_timeout(
                self.db_manager,
                "Pilih metode pembayaran (1: Tunai | 2: QRIS | 'x' untuk batal): ",
            )
            if payment_method_input.lower() == "x":
                print("❌ - Membatalkan proses pembayaran.\n")
                return False, None
            try:
                payment_method = int(payment_method_input)
                if payment_method == 1:
                    return self.process_cash_payment(total_price)
                elif payment_method == 2:
                    return self.process_qris_payment(total_price)
                else:
                    print(
                        "⚠ - Metode pembayaran tidak tersedia. Silakan pilih 1 atau 2."
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")
