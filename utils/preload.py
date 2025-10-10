import arcade.gui, arcade

button_texture = arcade.gui.NinePatchTexture(64 // 4, 64 // 4, 64 // 4, 64 // 4, arcade.load_texture("assets/graphics/button.png"))
button_hovered_texture = arcade.gui.NinePatchTexture(64 // 4, 64 // 4, 64 // 4, 64 // 4, arcade.load_texture("assets/graphics/button_hovered.png"))

light_wizard_spritesheet = arcade.load_spritesheet("assets/graphics/mage-light.png").get_texture_grid((48, 64), 3, 12)
light_wizard_up_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in light_wizard_spritesheet[0:2]])
light_wizard_right_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in light_wizard_spritesheet[3:5]])
light_wizard_standing_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in light_wizard_spritesheet[6:8]])
light_wizard_left_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in light_wizard_spritesheet[9:11]])

dark_wizard_spritesheet = arcade.load_spritesheet("assets/graphics/mage-dark.png").get_texture_grid((48, 64), 3, 12)
dark_wizard_up_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in dark_wizard_spritesheet[0:2]])
dark_wizard_right_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in dark_wizard_spritesheet[3:5]])
dark_wizard_standing_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in dark_wizard_spritesheet[6:8]])
dark_wizard_left_animation = arcade.TextureAnimation([arcade.TextureKeyframe(texture, 300) for texture in dark_wizard_spritesheet[9:11]])

irs_agent_texture = arcade.load_texture("assets/graphics/irs_agent.png")