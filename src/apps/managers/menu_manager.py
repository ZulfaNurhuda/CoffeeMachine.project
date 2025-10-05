"""
This file defines the `MenuManager` class, which is responsible for
handling the display and selection of the coffee menu.

Its primary tasks are:
- Assigning sequential numbers to available coffees for easy user selection.
- Displaying the formatted menu, including coffee names, prices, stock levels,
  and a special indicator for the bestselling coffee.
"""

from typing import Dict

from apps.data_classes import CoffeeData

class MenuManager:
    """
    Manages the display and selection of the coffee menu.
    
    It displays coffees with stock > 0 and marks the bestselling coffee.

    Attributes:
        coffee_list (Dict[str, CoffeeData]): A dictionary mapping coffee names to CoffeeData objects.
        bestselling_coffee_name (str): The name of the bestselling coffee.
    """

    def __init__(self, coffee_list: Dict[str, CoffeeData], bestselling_coffee_name: str = ""):
        """
        Initializes the MenuManager.

        Args:
            coffee_list (Dict[str, CoffeeData]): A dictionary mapping coffee names to CoffeeData objects.
            bestselling_coffee_name (str): The name of the bestselling coffee (default: "").
        """
        self.coffee_list = coffee_list
        self.bestselling_coffee_name = bestselling_coffee_name

    def set_coffee_numbers(self) -> None:
        """
        Assigns a sequential number to each coffee that has a stock greater than 0.
        This number is used for user selection from the menu.
        """
        number = 1
        for coffee in self.coffee_list.values():
            if coffee.stock > 0:
                coffee.number = number
                number += 1

    def display_coffee_menu(self) -> None:
        """
        Displays the available coffee menu.
        
        If a coffee is the bestseller, it adds a star symbol (★) next to its name.
        Only coffees with a positive stock level are displayed.
        """
        print("================ Menu Kopi =================")
        for coffee in self.coffee_list.values():
            if coffee.stock > 0:
                star = " ★" if coffee.name == self.bestselling_coffee_name else ""
                print(
                    f"{coffee.number}. {coffee.name}{star} - Rp{coffee.price} - Persediaan: {coffee.stock}"
                )
        print("=============================================")
