import arcade, arcade.gui, os, json

from math import ceil

from wizard_vs_irs.utils.constants import button_style, SHOP_ITEMS
from wizard_vs_irs.utils.preload import button_texture, button_hovered_texture

class Shop(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

        self.pypresence_client = pypresence_client
    
        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.grid = self.anchor.add(arcade.gui.UIGridLayout(column_count=4, row_count=ceil(len(SHOP_ITEMS) / 4), horizontal_spacing=10, vertical_spacing=10), anchor_x="center", anchor_y="center")

        if os.path.exists("data.json"):
            with open("data.json", "r") as file:
                self.data = json.load(file)
        else:
            self.data = {}

        if not "shop" in self.data:
            self.data["shop"] = {}
    
        self.shop_buttons = []

    def main_exit(self):
        with open("data.json", "w") as file:
            file.write(json.dumps(self.data, indent=4))

        from wizard_vs_irs.menus.main import Main
        self.window.show_view(Main(self.pypresence_client))

    def on_show_view(self):
        super().on_show_view()

        self.back_button = arcade.gui.UITextureButton(texture=button_texture, texture_hovered=button_hovered_texture, text='<--', style=button_style, width=100, height=50)
        self.back_button.on_click = lambda event: self.main_exit()
        self.anchor.add(self.back_button, anchor_x="left", anchor_y="top", align_x=5, align_y=-5)

        self.evaded_tax_label = self.anchor.add(arcade.gui.UILabel(f"Evaded Tax: {self.data['evaded_tax']}$", font_size=24), anchor_x="center", anchor_y="top")

        for n, shop_item in enumerate(SHOP_ITEMS):
            row, col = n // 4, n % 4

            if not shop_item[1] in self.data["shop"]:
                self.data["shop"][shop_item[1]] = 0

            upgrade_cost = (self.data["shop"][shop_item[1]] + 1) * shop_item[3]

            max_count = shop_item[2]

            notice_string = "\n(Also increases knockback)" if "DMG" in shop_item[0] else ""
            level_string = self.data["shop"][shop_item[1]] if self.data["shop"][shop_item[1]] < max_count else "Max"

            button = self.grid.add(arcade.gui.UITextureButton(
                text=f'{shop_item[0]}{notice_string}\nLevel: {level_string}\nUpgrade Cost: {upgrade_cost}$',
                texture=button_texture,
                texture_hovered=button_hovered_texture,
                style=button_style,
                width=self.window.width / 8,
                height=self.window.width / 8,
                multiline=True,
                align="center"
            ), row=row, column=col)

            self.shop_buttons.append(button)

            button.on_click = lambda event, n=n: self.buy_upgrade(n)

    def buy_upgrade(self, n):
        item_list = SHOP_ITEMS[n]
        json_name = item_list[1]
        max_count = item_list[2]

        current_level = self.data["shop"][json_name]
        cost = (current_level + 1) * item_list[3]

        if not self.data["evaded_tax"] >= cost:
            return
        
        if current_level >= item_list[2]:
            return

        self.data["shop"][json_name] += 1
        self.data["evaded_tax"] -= cost

        notice_string = "\n(Also increases knockback)" if "DMG" in item_list[0] else ""
        level_string = self.data["shop"][item_list[1]] if self.data["shop"][item_list[1]] < max_count else "Max"

        self.shop_buttons[n].text = f"{item_list[0]}{notice_string}\nLevel: {level_string}\nUpgrade Cost: {cost + item_list[3]}"
        self.evaded_tax_label.text = f"Evaded Tax: {self.data['evaded_tax']}$"

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.main_exit()