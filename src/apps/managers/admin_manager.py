"""
This file defines the `AdminManager` class, which is responsible for handling
all administrative functionalities of the coffee machine. This includes
authenticating the admin, restocking supplies, changing the admin code,
and shutting down the program safely.

Key functionalities include:
- `authenticate_admin`: Prompts for and verifies the admin code.
- `restock_coffee`: Manages the user interface for restocking coffee beans.
- `restock_additives`: Manages the user interface for restocking additives like sugar and milk.
- `change_admin_code`: Allows a logged-in admin to change the access code.
- `shutdown_program`: Safely shuts down the application after saving all pending changes.
"""

from apps.database.database_manager import DatabaseManager
from apps.utils.input_utils import input_with_timeout

class AdminManager:
    """
    Manages admin features: restocking, changing admin code, and program shutdown.
    Ensures admin authentication before proceeding with any action.

    Attributes:
        db_manager (DatabaseManager): The database manager object to interact with the database.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the AdminManager.

        Args:
            db_manager (DatabaseManager): The DatabaseManager object to interact with the database.
        """
        self.db_manager = db_manager

    def authenticate_admin(self) -> bool:
        """
        Prompts for the admin code and performs authentication.
        Allows a maximum of 5 attempts.

        Returns:
            bool: True if authentication is successful, False if it fails or is canceled.
        """
        max_attempts = 5
        attempts = 0
        while attempts < max_attempts:
            code_input = input_with_timeout(
                self.db_manager, "Masukkan kode admin ('x' untuk batal): "
            )
            if code_input.lower() == "x":
                print("❌ - Membatalkan aksi admin.\n")
                return False
            try:
                code = int(code_input)
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")
                attempts += 1
                continue

            if code == self.db_manager.admin_code:
                print("✅ - Autentikasi berhasil.\n")
                return True
            else:
                attempts += 1
                print(
                    f"⚠ - Kode admin salah! {max_attempts - attempts} percobaan tersisa."
                )
        print("⚠ - Autentikasi administrator gagal.\n")
        return False

    def restock_coffee(self) -> None:
        """
        Handles the coffee restocking process for the admin.
        Adds the specified amount of stock for a selected coffee type.
        """
        print("\n*********** Menu Restock Kopi ************")
        coffee_list = self.db_manager.coffee_list
        while True:
            print("==== Daftar Kopi ====")
            number_map = {}
            number = 1
            for coffee in coffee_list.values():
                if coffee.stock >= 0:
                    print(f"{number}. {coffee.name} - Stok: {coffee.stock}")
                    number_map[number] = coffee
                    number += 1
            print("=====================")

            coffee_choice_input = input_with_timeout(
                self.db_manager, "Pilih kopi untuk restock ('x' untuk batal): "
            )
            if coffee_choice_input.lower() == "x":
                print("❌ - Membatalkan restock kopi.\n")
                return
            if not coffee_choice_input.isdigit():
                print("⚠ - Masukkan nomor kopi atau 'x' untuk batal.")
                continue
            coffee_choice = int(coffee_choice_input)
            if coffee_choice not in number_map:
                print("⚠ - Nomor kopi tidak valid.")
                continue
            coffee = number_map[coffee_choice]

            # Get the restock amount
            while True:
                restock_amount_input = input_with_timeout(
                    self.db_manager,
                    f"Masukkan jumlah restock untuk {coffee.name} ('x' untuk batal): ",
                )
                if restock_amount_input.lower() == "x":
                    print("❌ - Membatalkan restock kopi.\n")
                    return
                try:
                    restock_amount = int(restock_amount_input)
                    if restock_amount <= 0:
                        print("⚠ - Jumlah restock harus > 0.")
                        continue
                    # Use the synchronous method for restocking
                    self.db_manager.restock_coffee_sync(coffee.name, restock_amount)
                    print(
                        f"✅ - Berhasil restock {coffee.name} sebanyak {restock_amount}.\n"
                    )
                    break
                except ValueError:
                    print("⚠ - Masukkan harus berupa angka.")

            more_input = input_with_timeout(
                self.db_manager, "\nApakah ingin melakukan restock lagi? (y/n): "
            ).lower()
            if more_input in ["y", "ya"]:
                continue
            else:
                print("\n🔃 - Kembali ke submenu admin.\n")
                return

    def restock_additives(self) -> None:
        """
        Handles the additive restocking process for the admin.
        Adds the specified amount of stock for a selected additive.
        """
        print("\n*********** Menu Restock Bahan Tambahan ************")
        additives_list = self.db_manager.additives_list
        while True:
            print("==== Daftar Bahan Tambahan ====")
            number_map = {}
            number = 1
            for additive, stock in additives_list.items():
                print(f"{number}. {additive} - Stok: {stock}")
                number_map[number] = additive
                number += 1
            print("===============================")

            additive_choice_input = input_with_timeout(
                self.db_manager,
                "Pilih bahan tambahan untuk restock ('x' untuk batal): ",
            )
            if additive_choice_input.lower() == "x":
                print("❌ - Membatalkan restock bahan tambahan.\n")
                return
            if not additive_choice_input.isdigit():
                print("⚠ - Masukkan nomor bahan tambahan atau 'x' untuk batal.")
                continue
            additive_choice = int(additive_choice_input)
            if additive_choice not in number_map:
                print("⚠ - Nomor bahan tambahan tidak valid.")
                continue
            additive = number_map[additive_choice]

            # Get the restock amount
            while True:
                restock_amount_input = input_with_timeout(
                    self.db_manager,
                    f"Masukkan jumlah restock untuk {additive} ('x' untuk batal): ",
                )
                if restock_amount_input.lower() == "x":
                    print("❌ - Membatalkan restock bahan tambahan.\n")
                    return
                try:
                    restock_amount = int(restock_amount_input)
                    if restock_amount <= 0:
                        print("⚠ - Jumlah restock harus > 0.")
                        continue
                    # Use the synchronous method for restocking
                    self.db_manager.restock_additives_sync(additive, restock_amount)
                    print(
                        f"✅ - Berhasil restock {additive} sebanyak {restock_amount} takaran.\n"
                    )
                    break
                except ValueError:
                    print("⚠ - Masukkan harus berupa angka.")

            more_input = input_with_timeout(
                self.db_manager, "\nApakah ingin melakukan restock lagi? (y/n): "
            ).lower()
            if more_input in ["y", "ya"]:
                continue
            else:
                print("\n🔃 - Kembali ke submenu admin.\n")
                return

    def change_admin_code(self) -> None:
        """
        Changes the admin code permanently.
        This can only be done by an already authenticated admin.
        """
        print("\n*********** Ganti Kode Admin ************")
        while True:
            new_code_input = input_with_timeout(
                self.db_manager, "Masukkan kode admin baru ('x' untuk batal): "
            )
            if new_code_input.lower() == "x":
                print("❌ - Membatalkan penggantian kode admin.\n")
                return
            try:
                new_code = int(new_code_input)
                if new_code > 0:
                    self.db_manager.save_admin_code(new_code)
                    print("✅ - Kode admin berhasil diganti.\n")
                    return
                else:
                    print("⚠ - Kode admin harus > 0.")
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")

    def shutdown_program(self) -> None:
        """
        Shuts down the program after admin authentication.
        If authentication is successful, the program exits after a final sync.
        """
        print("\n*********** Menonaktifkan Program ************")
        print("💤 - Mesin kopi bersiap untuk dimatikan. Menyimpan perubahan terakhir...")
        self.db_manager.save_changes_before_exit()
        print("👋 - Mesin kopi berhasil dimatikan.")

        import sys
        sys.exit(0)
