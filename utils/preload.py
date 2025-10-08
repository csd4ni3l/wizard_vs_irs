import arcade.gui, arcade

button_texture = arcade.gui.NinePatchTexture(64 // 4, 64 // 4, 64 // 4, 64 // 4, arcade.load_texture("assets/graphics/button.png"))
button_hovered_texture = arcade.gui.NinePatchTexture(64 // 4, 64 // 4, 64 // 4, 64 // 4, arcade.load_texture("assets/graphics/button_hovered.png"))
wizard_texture = arcade.texture.make_soft_square_texture(100, arcade.color.BLACK, outer_alpha=255)
irs_agent_texture = arcade.texture.make_soft_square_texture(30, arcade.color.RED, outer_alpha=255)