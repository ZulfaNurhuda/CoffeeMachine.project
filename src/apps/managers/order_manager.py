"""
This file defines the `OrderManager` class, which is responsible for managing
the user's coffee ordering process. It guides the user through selecting a coffee,
choosing the temperature, customizing the composition of additives, and specifying
the quantity.

Key functionalities include:
- Interacting with the user to get their coffee selection, temperature preference,
  and desired amount of additives (sugar, creamer, milk, chocolate).
- Validating user input and checking stock availability for both coffee and additives
  before confirming an order item.
- Aggregating multiple items into a single order.
- Displaying a summary of the order with the total price.
- Handling order cancellations and modifications.
"""

from typing import Dict, List, Optional

from apps.managers.menu_manager import MenuManager
from apps.database.database_manager import DatabaseManager
from apps.data_classes import CoffeeData, CompositionData, OrderItem
from apps.utils.input_utils import input_with_timeout

class OrderManager:
    """
    Manages the coffee ordering process for the user.
    Checks coffee and additive stock before confirming the order.

    Attributes:
        db_manager (DatabaseManager): The database manager object.
        coffee_list (Dict[str, CoffeeData]): A dictionary of available coffees.
        menu_manager (MenuManager): The menu manager object.
        additives_list (Dict[str, int]): A dictionary of available additives and their stock.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        coffee_list: Dict[str, CoffeeData],
        menu_manager: MenuManager,
        additives_list: Dict[str, int],
    ):
        """
        Initializes the OrderManager.

        Args:
            db_manager (DatabaseManager): The DatabaseManager object to interact with the database.
            coffee_list (Dict[str, CoffeeData]): A dictionary mapping coffee names to CoffeeData objects.
            menu_manager (MenuManager): The MenuManager object to manage the menu display.
            additives_list (Dict[str, int]): A dictionary mapping additive names to their remaining stock.
        """
        self.db_manager = db_manager
        self.coffee_list = coffee_list
        self.menu_manager = menu_manager
        self.additives_list = additives_list

    def select_temperature(self, coffee_name: str) -> Optional[str]:
        """
        Prompts the user to select the coffee temperature.
        1 = Hot, 2 = Cold.

        Args:
            coffee_name (str): The name of the selected coffee.

        Returns:
            Optional[str]: 'hangat' or 'dingin', or None if canceled.
        """
        while True:
            temp_input = input_with_timeout(
                self.db_manager,
                f"🌡 - Tentukan suhu untuk {coffee_name}? (1. Hangat | 2. Dingin | 'x' untuk batal): ",
            )
            if temp_input.lower() == "x":
                print("❌ - Membatalkan pemilihan suhu.")
                return None
            elif temp_input == "1":
                return "hangat"
            elif temp_input == "2":
                return "dingin"
            else:
                print("⚠ - Input tidak valid. Silakan masukkan '1' atau '2'.")

    def set_additive_amount(self, additive_type: str) -> Optional[int]:
        """
        Prompts the user to set the amount of an additive (0-5 units).

        Args:
            additive_type (str): The type of additive to be configured.

        Returns:
            Optional[int]: The amount of the additive, or None if canceled.
        """
        while True:
            # Display the available stock of the additive before asking for input
            available_stock = self.additives_list.get(additive_type, 0)
            print(f"📦 - Stok {additive_type}: {available_stock} takaran")

            amount_input = input_with_timeout(
                self.db_manager,
                f"> 🎨 - Atur kadar {additive_type} (0-5 takaran | 'x' untuk batal): ",
            )
            if amount_input.lower() == "x":
                print("❌ - Membatalkan pengaturan komposisi.")
                return None
            try:
                amount = int(amount_input)
                if 0 <= amount <= 5:
                    # Validate that the chosen amount does not exceed the available stock
                    if amount > available_stock:
                        print(
                            f"⚠ - Jumlah takaran {additive_type} melebihi stok yang tersedia ({available_stock})."
                        )
                        continue
                    return amount
                else:
                    print("⚠ - Jumlah harus antara 0 hingga 5.")
            except ValueError:
                print("⚠ - Input tidak valid. Masukkan angka.")

    def select_composition(self) -> Optional[CompositionData]:
        """
        Guides the user through selecting the composition of sugar, creamer, milk, and chocolate.

        Returns:
            Optional[CompositionData]: A CompositionData object with the additive composition, or None if canceled.
        """
        sugar = self.set_additive_amount("Gula")
        if sugar is None:
            return None
        creamer = self.set_additive_amount("Krimer")
        if creamer is None:
            return None
        milk = self.set_additive_amount("Susu")
        if milk is None:
            return None
        chocolate = self.set_additive_amount("Cokelat")
        if chocolate is None:
            return None
        return CompositionData(sugar, creamer, milk, chocolate)

    def order_quantity(self) -> Optional[int]:
        """
        Prompts the user to specify the number of coffees to order.

        Returns:
            Optional[int]: The number of coffees ordered (> 0), or None if canceled.
        """
        while True:
            quantity_input = input_with_timeout(
                self.db_manager,
                "Pesan berapa kopi dengan komposisi ini? ('x' untuk batal): ",
            )
            if quantity_input.lower() == "x":
                print("❌ - Membatalkan pemesanan.\n")
                return None
            try:
                quantity = int(quantity_input)
                if quantity > 0:
                    return quantity
                else:
                    print("⚠ - Jumlah kopi harus lebih dari 0.")
            except ValueError:
                print("⚠ - Input tidak valid. Masukkan angka.")

    def are_compositions_equal(self, comp1: CompositionData, comp2: CompositionData) -> bool:
        """
        Compares two additive compositions.

        Args:
            comp1 (CompositionData): The first composition.
            comp2 (CompositionData): The second composition.

        Returns:
            bool: True if both compositions are the same, False otherwise.
        """
        return comp1 == comp2

    def add_to_order(
        self,
        order_data: List[OrderItem],
        coffee: CoffeeData,
        temperature: str,
        composition: CompositionData,
        quantity: int,
    ) -> List[OrderItem]:
        """
        Adds an order item to the order list.
        If an item with the same composition already exists, its quantity is increased.

        Args:
            order_data (List[OrderItem]): The current list of order items.
            coffee (CoffeeData): The CoffeeData object being ordered.
            temperature (str): The temperature of the coffee.
            composition (CompositionData): The additive composition.
            quantity (int): The quantity of the coffee being ordered.

        Returns:
            List[OrderItem]: The updated list of order items.
        """
        existing = next(
            (
                item
                for item in order_data
                if item.coffee.name == coffee.name
                and item.temperature == temperature
                and self.are_compositions_equal(item.composition, composition)
            ),
            None,
        )
        if existing:
            existing.quantity += quantity
        else:
            order_data.append(OrderItem(coffee, quantity, temperature, composition))
        return order_data

    def summarize_order(self, order: List[OrderItem]) -> int:
        """
        Displays a summary of the order and calculates the total price.

        Args:
            order (List[OrderItem]): The list of order items.

        Returns:
            int: The total price of the order.
        """
        print("========== Ringkasan Pesanan ==========")
        total_price = 0
        for idx, item in enumerate(order, 1):
            coffee_price = item.coffee.price * item.quantity
            total_price += coffee_price
            print(
                f"{idx}. {item.coffee.name} ({item.temperature}) x{item.quantity} - Rp{coffee_price}"
            )
            print(
                f"   Gula: {item.composition.sugar} takaran, "
                f"Krimer: {item.composition.creamer} takaran, "
                f"Susu: {item.composition.milk} takaran, "
                f"Cokelat: {item.composition.chocolate} takaran"
            )
        print(f">>> Total Harga: Rp{total_price}")
        print("=======================================")
        return total_price

    def check_additive_stock(self, composition: CompositionData, quantity: int) -> bool:
        """
        Checks the availability of additives.

        Args:
            composition (CompositionData): The desired additive composition.
            quantity (int): The number of coffees being ordered.

        Returns:
            bool: True if the additive stock is sufficient, False otherwise.
        """
        needed_sugar = composition.sugar * quantity
        needed_creamer = composition.creamer * quantity
        needed_milk = composition.milk * quantity
        needed_chocolate = composition.chocolate * quantity

        if self.additives_list.get("Gula", 0) < needed_sugar:
            print(
                f"☕ - Stok Gula tidak mencukupi. Tersisa {self.additives_list.get('Gula', 0)}."
            )
            return False
        if self.additives_list.get("Krimer", 0) < needed_creamer:
            print(
                f"☕ - Stok Krimer tidak mencukupi. Tersisa {self.additives_list.get('Krimer', 0)}."
            )
            return False
        if self.additives_list.get("Susu", 0) < needed_milk:
            print(
                f"☕ - Stok Susu tidak mencukupi. Tersisa {self.additives_list.get('Susu', 0)}."
            )
            return False
        if self.additives_list.get("Cokelat", 0) < needed_chocolate:
            print(
                f"☕ - Stok Cokelat tidak mencukupi. Tersisa {self.additives_list.get('Cokelat', 0)}."
            )
            return False

        return True

    def select_coffee(self) -> List[OrderItem]:
        """
        Handles the user's coffee selection process.

        Returns:
            List[OrderItem]: A list of order items, or an empty list if canceled.
        """
        coffee_name_by_number = {
            coffee.number: coffee for coffee in self.coffee_list.values() if coffee.stock > 0
        }
        order_data: List[OrderItem] = []
        order_count = 1
        while True:
            print(f"\n*********** Pesanan ke-{order_count}: Pilih Kopi ************")
            self.menu_manager.display_coffee_menu()
            choice = input_with_timeout(
                self.db_manager, "Pilih nomor kopi ('x' untuk batal): "
            )
            if choice.lower() == "x":
                print("❌ - Membatalkan proses pemesanan.\n")
                if (len(order_data) > 0):
                    for item in order_data:
                        self.coffee_list[item.coffee.name].stock += item.quantity
                        self.additives_list["Gula"] += item.composition.sugar * item.quantity
                        self.additives_list["Krimer"] += item.composition.creamer * item.quantity
                        self.additives_list["Susu"] += item.composition.milk * item.quantity
                        self.additives_list["Cokelat"] += item.composition.chocolate * item.quantity
                order_data = []
                break
            elif choice.isdigit():
                choice_int = int(choice)
                if choice_int in coffee_name_by_number:
                    coffee = coffee_name_by_number[choice_int]
                    print(f"\nAnda memilih {coffee.name}".upper())
                    temperature = self.select_temperature(coffee.name)
                    if temperature is None:
                        continue
                    composition = self.select_composition()
                    if composition is None:
                        continue
                    quantity = self.order_quantity()
                    if quantity is None:
                        continue

                    # Check coffee stock
                    if coffee.stock < quantity:
                        print(
                            f"☕ - Stok {coffee.name} tidak mencukupi. Tersisa {coffee.stock}."
                        )
                        print(
                            "🔃 - Silakan ulangi pemesanan dengan jumlah yang tersedia.\n"
                        )
                        continue

                    # Check additive stock
                    if not self.check_additive_stock(composition, quantity):
                        print(
                            "🔃 - Silakan ulangi pemesanan dengan komposisi yang tersedia.\n"
                        )
                        continue

                    # If stock is sufficient, add to the order data
                    order_data = self.add_to_order(
                        order_data, coffee, temperature, composition, quantity
                    )

                    print("\nApakah Anda ingin memesan kopi lagi?")
                    more = input_with_timeout(
                        self.db_manager, "Ketik 'y' untuk Ya atau 'n' untuk Tidak: "
                    ).lower()

                    if more in ["n", "no", "tidak", "gak"]:
                        print("\nMelanjutkan ke proses pembayaran...")
                        break
                    else:
                        order_count += 1
            
                    # Update stock after all orders are confirmed
                    for item in order_data:
                        self.coffee_list[item.coffee.name].stock -= item.quantity
                        self.additives_list["Gula"] -= item.composition.sugar * item.quantity
                        self.additives_list["Krimer"] -= item.composition.creamer * item.quantity
                        self.additives_list["Susu"] -= item.composition.milk * item.quantity
                        self.additives_list["Cokelat"] -= item.composition.chocolate * item.quantity
                else:
                    print("⚠ - Pilihan tidak tersedia. Silakan pilih lagi.")
            else:
                print("⚠ - Input tidak valid. Silakan masukkan angka atau 'x'.")
        return order_data
