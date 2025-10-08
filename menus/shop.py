import arcade, arcade.gui

from utils.constants import button_style, SHOP_ITEMS
from utils.preload import button_texture, button_hovered_texture

class Shop(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

        self.pypresence_client = pypresence_client
    
        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.grid = self.anchor.add(arcade.gui.UIGridLayout(size_hint=(0.75, 0.75), column_count=4, row_count=999), anchor_x="center", anchor_y="center")

    def on_show_view(self):
        super().on_show_view()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            from menus.main import Main
            self.window.show_view(Main(self.pypresence_client))