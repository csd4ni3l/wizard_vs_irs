import arcade, arcade.gui

from wizard_vs_irs.utils.constants import button_style

class Inventory(arcade.gui.UIBoxLayout):
    def __init__(self, items, window_width):
        super().__init__(size_hint=(0.5, 0.1), vertical=False, space_between=5)
        self.items = items
        self.current_inventory_item = 0

        self.inventory_buttons: list[arcade.gui.UITextureButton] = []

        for n, item in enumerate(items):
            self.inventory_buttons.append(self.add(arcade.gui.UIFlatButton(text=f"{item[0]} ({n + 1})", style=button_style, width=(window_width * 0.5) / len(items) + 1)))

        self.pay_tax_button = self.add(arcade.gui.UIFlatButton(text="Pay Tax (1000$)", style=button_style, width=(window_width * 0.5) / len(items) + 1))
        self.pay_tax_button.style["normal"]["bg"] = arcade.color.GRAY
        self.pay_tax_button.style["normal"]["bg"] = arcade.color.GRAY

        self.update_selection()

    def update_selection(self):
        for n in range(len(self.items)):
            if n == self.current_inventory_item:
                self.inventory_buttons[n].style["normal"] = arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.WHITE, font_color=arcade.color.BLACK)
            else:
                self.inventory_buttons[n].style["normal"] = arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.GRAY, font_color=arcade.color.BLACK)

            self.inventory_buttons[n]._requires_render = True

    def select_item(self, number):
        self.current_inventory_item = number
        self.update_selection()