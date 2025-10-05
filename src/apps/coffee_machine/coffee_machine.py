"""
This file defines the `CoffeeMachine` class, which is the core of the coffee machine application.
This class acts as the main orchestrator that integrates various managers (such as menu, order, payment, and admin)
to simulate the entire operational flow of the coffee machine.

Key functionalities covered by this class include:
- Initializing all manager components with data from the `DatabaseManager`.
- Running the main simulation loop that displays the menu to the user.
- Directing user choices to the appropriate flow (ordering, scanning QR, admin menu).
- Managing the ordering flow from start to finish, including stock validation,
  payment processing, and transaction logging.
"""

from apps.database.database_manager import DatabaseManager
from apps.managers.menu_manager import MenuManager
from apps.managers.order_manager import OrderManager
from apps.managers.payment_manager import PaymentManager
from apps.managers.online_order_manager import OnlineOrderManager
from apps.managers.admin_manager import AdminManager
from apps.data_classes import SalesRecord, CoffeeData
from apps.utils.input_utils import input_with_timeout

class CoffeeMachine:
    """
    The main class that orchestrates the entire functionality of the coffee machine.

    This class integrates all managers to provide a complete workflow,
    from user interaction, order processing, payment,
    to administrative features.

    Attributes:
        db_manager (DatabaseManager): The data manager connected to Google Sheets.
        coffee_list (Dict[str, CoffeeData]): Local cache for coffee inventory data.
        additives_list (Dict[str, int]): Local cache for additive inventory data.
        menu_manager (MenuManager): Manages the display of the coffee menu.
        order_manager (OrderManager): Manages the ordering logic.
        scan_qr_manager (OnlineOrderManager): Manages orders from QR code scans.
        admin_manager (AdminManager): Manages administrative functions.
        payment_manager (PaymentManager): Manages the payment process.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the CoffeeMachine and all necessary managers.

        Args:
            db_manager (DatabaseManager): An instance of `DatabaseManager` that is already
                                       connected and contains initial data.
        """
        self.db_manager = db_manager
        self.coffee_list = db_manager.coffee_list
        self.additives_list = db_manager.additives_list

        # Determine the best-selling coffee to feature on the menu
        bestseller = self.db_manager.get_bestselling_coffee()

        # Initialize all managers with the relevant data
        self.menu_manager = MenuManager(self.coffee_list, bestseller)
        self.menu_manager.set_coffee_numbers()

        self.order_manager = OrderManager(
            self.db_manager, self.coffee_list, self.menu_manager, self.additives_list
        )
        self.scan_qr_manager = OnlineOrderManager(
            self.db_manager, self.order_manager
        )
        self.admin_manager = AdminManager(self.db_manager)
        self.payment_manager = PaymentManager(self.db_manager)

    def simulation(self) -> None:
        """
        Runs the main simulation loop of the coffee machine.

        Displays the main menu to the user (Order, Scan QR, Admin)
        and handles user input continuously until the program is terminated.
        """
        print("\n=== Selamat datang di Mesin Kopi Virtual! ===\n")
        while True:
            print("======= Pilihan Menu =======")
            print("1. Mulai Pemesanan")
            print("2. Scan QR")
            print("3. Menu Admin")
            print("============================")
            choice = input("Pilih opsi (1, 2, 3): ")
            if choice == "1":
                self.start_order()
            elif choice == "2":
                self.scan_qr_manager.scan_qr()
            elif choice == "3":
                self.admin_menu()
            else:
                print("⚠ - Pilihan tidak valid. Silakan pilih 1, 2, atau 3.")

    def admin_menu(self) -> None:
        """
        Displays and manages the administrative menu.

        This function requires admin authentication before granting access to
        sub-menus like restocking, changing the admin code, or shutting down the program.
        """
        print("\n*********** Menu Admin ************")
        authenticated = self.admin_manager.authenticate_admin()
        if not authenticated:
            return

        while True:
            print("\n======= Submenu Admin =======")
            print("1. Restock Kopi")
            print("2. Restock Bahan Tambahan")
            print("3. Ganti Kode Admin")
            print("4. Matikan Program")
            print("5. Kembali ke Menu Utama")
            print("==============================")
            choice = input_with_timeout(
                self.db_manager, "Pilih opsi admin (1, 2, 3, 4, 5): "
            )
            if choice == "1":
                self.admin_manager.restock_coffee()
            elif choice == "2":
                self.admin_manager.restock_additives()
            elif choice == "3":
                self.admin_manager.change_admin_code()
            elif choice == "4":
                self.admin_manager.shutdown_program()
            elif choice == "5":
                print("\n🔃 - Kembali ke menu utama.\n")
                break
            else:
                print("⚠ - Pilihan tidak valid. Silakan pilih 1, 2, 3, 4, atau 5.")

    def start_order(self) -> None:
        """
        Manages the entire coffee ordering flow for the user.

        This process includes:
        1. Ensuring that coffee is available.
        2. Guiding the user through selecting coffee, temperature, and composition.
        3. Validating the availability of coffee stock and additives.
        4. Processing the payment after the order is confirmed.
        5. Enqueuing stock updates and sales logging if the payment is successful.
        6. Updating the local data cache to maintain consistency.
        """
        if not self.coffee_list:
            print("\n💔 - Mohon maaf, tidak ada kopi yang tersedia saat ini.\n")
            return
        
        order = self.order_manager.select_coffee()
        if order:
            # Perform a final stock check to ensure there are no conflicts
            stock_sufficient = True
            for item in order:
                if item.coffee.stock < item.quantity:
                    print(
                        f"☕ - Stok {item.coffee.name} tidak cukup. Tersisa {item.coffee.stock}."
                    )
                    stock_sufficient = False
                    break
                if not self.order_manager.check_additive_stock(
                    item.composition, item.quantity
                ):
                    stock_sufficient = False
                    break

            if not stock_sufficient:
                print("🔃 - Silakan ulangi pemesanan.\n")
                return

            total_price = self.order_manager.summarize_order(order)
            payment_successful, method = self.payment_manager.process_payment(
                total_price
            )

            if payment_successful:
                print("☕ - Terima kasih! Silakan ambil kopi Anda.\n")
                # Process after successful payment
                for item in order:
                    # 1. Log the sale
                    sales_record = SalesRecord(
                        coffee_type=item.coffee.name,
                        temperature=item.temperature,
                        composition=f"Gula ({item.composition.sugar}), "
                        f"Susu ({item.composition.milk}), "
                        f"Krimer ({item.composition.creamer}), "
                        f"Cokelat ({item.composition.chocolate})",
                        quantity=f"x{item.quantity}",
                        total_price=item.coffee.price * item.quantity,
                        payment_method=method,
                    )
                    self.db_manager.enqueue_log_sale(sales_record)

                    # 2. Decrease coffee stock
                    self.db_manager.enqueue_update_stock(item.coffee.name, item.quantity)

                    # 3. Decrease additive stock
                    self.db_manager.enqueue_update_additive(
                        "Gula", -(item.composition.sugar * item.quantity)
                    )
                    self.db_manager.enqueue_update_additive(
                        "Krimer", -(item.composition.creamer * item.quantity)
                    )
                    self.db_manager.enqueue_update_additive(
                        "Susu", -(item.composition.milk * item.quantity)
                    )
                    self.db_manager.enqueue_update_additive(
                        "Cokelat", -(item.composition.chocolate * item.quantity)
                    )

                # Update local cache to reflect changes
                self.coffee_list = self.db_manager.coffee_list
                self.additives_list = self.db_manager.additives_list
                bestseller = self.db_manager.get_bestselling_coffee()
                self.menu_manager = MenuManager(self.coffee_list, bestseller)
                self.menu_manager.set_coffee_numbers()
            else:
                if method is None:
                    print("💰 - Pembayaran dibatalkan.\n")
                else:
                    print("📉 - Pembayaran gagal.\n")
        else:
            print("📃 - Tidak ada pesanan. Kembali ke menu utama.\n")

