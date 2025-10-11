import arcade, arcade.gui, random, math, time, json, math

from utils.constants import BULLET_SPEED, IRS_AGENT_HEALTH, HEALTH_INCREASE_PER_LEVEL, PLAYER_SPEED, IRS_AGENT_SPEED, TAX_PER_IRS_AGENT, IRS_AGENT_ATTACK_SPEED
from utils.constants import IRS_AGENT_SPAWN_INTERVAL, SPAWN_INTERVAL_DECREASE_PER_LEVEL, SPEED_INCREASE_PER_LEVEL, item_to_json_name
from utils.constants import TAX_EVASION_LEVELS, TAX_EVASION_NAMES, TAX_INCREASE_PER_LEVEL, menu_background_color, INVENTORY_ITEMS, INVENTORY_TRIGGER_KEYS, PLAYER_INACCURACY_MAX

import utils.preload
from utils.preload import irs_agent_texture
from utils.preload import light_wizard_left_animation, light_wizard_right_animation, light_wizard_standing_animation, light_wizard_up_animation
from utils.preload import dark_wizard_left_animation, dark_wizard_right_animation, dark_wizard_standing_animation, dark_wizard_up_animation

from game.inventory import Inventory

class Bullet(arcade.Sprite):
    def __init__(self, radius, texture, x, y, direction):
        super().__init__(texture, center_x=x, center_y=y)
        self.radius = radius
        self.direction = direction
        self.speed = 0

    def move(self):
        self.position += self.direction * self.speed

class IRSAgent(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(irs_agent_texture, center_x=x, center_y=y, scale=1.25)

        self.damaged = False
        self.last_damage = time.perf_counter()
        self.last_attack = time.perf_counter()
        self.health = 0

    def update(self):
        if self.damaged:
            if time.perf_counter() - self.last_damage >= 0.3:
                self.damaged = False

            self.color = arcade.color.RED
        else:
            self.color = (255, 255, 255, 255)

class Player(arcade.TextureAnimationSprite):
    def __init__(self, x, y, dark_mode_unlocked=False): # x, y here because we dont know window width and height
        super().__init__(animation=dark_wizard_standing_animation if dark_mode_unlocked else light_wizard_standing_animation, center_x=x, center_y=y, scale=1.5)

        self.direction = arcade.math.Vec2()

class Game(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

        arcade.set_background_color(arcade.color.WHITE)

        self.pypresence_client = pypresence_client
        self.pypresence_client.update(state="Playing the game")

        with open("data.json", "r") as file: # no need for if, since Main already creates the file with default values.
            self.data = json.load(file)

        self.camera = arcade.Camera2D()

        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.camera.view_data,
            max_amplitude=10.0,
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )

        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.spritelist = arcade.SpriteList()

        self.irs_agents: list[IRSAgent] = []
        self.last_irs_agent_spawn = time.perf_counter()
        self.last_mana = time.perf_counter()
        self.last_shoot = time.perf_counter()

        self.evaded_tax = 0
        self.high_score = self.data["high_score"]
        self.mana = 0
        self.tax_evasion_level = TAX_EVASION_NAMES[0]

        self.bullets: list[Bullet] = []
        self.player = Player(self.window.width / 2, self.window.height / 2, self.data["shop"]["dark_mode_wizard"])
        self.spritelist.append(self.player)

        self.info_box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=0, align="left"), anchor_x="left", anchor_y="top")
        self.evaded_tax_label = self.info_box.add(arcade.gui.UILabel(text="Evaded Tax: 0$", font_size=14, text_color=arcade.color.BLACK))
        self.high_score_label = self.info_box.add(arcade.gui.UILabel(text=f"High Score: {self.high_score}$", font_size=14, text_color=arcade.color.BLACK))
        self.mana_label = self.info_box.add(arcade.gui.UILabel(text="Mana: 0", font_size=14, text_color=arcade.color.BLACK))
        self.tax_evasion_label = self.info_box.add(arcade.gui.UILabel(text=f"Tax Evasion Level: {self.tax_evasion_level}", font_size=14, text_color=arcade.color.BLACK))
        
        self.tax_evasion_level_notice = self.anchor.add(arcade.gui.UILabel(text="Tax Evasion Level Increased to example", font_size=28, text_color=arcade.color.BLACK), anchor_x="center", anchor_y="top")
        self.tax_evasion_level_notice.visible = False
        self.last_tax_evasion_notice = time.perf_counter()

        self.progress_bar = self.anchor.add(arcade.gui.UISlider(value=0, max_value=100, size_hint=(0.5, 0.15)), anchor_x="center", anchor_y="top")
        self.progress_bar._render_steps = lambda surface: None
        self.progress_bar._render_thumb = lambda surface: None
        self.progress_bar.on_event = lambda event: None

        self.inventory = self.anchor.add(Inventory(INVENTORY_ITEMS, self.window.width), anchor_x="left", anchor_y="bottom", align_x=self.window.width / 20)
        self.inventory.pay_tax_button.on_click = lambda event: self.pay_tax()

    def dash(self):
        self.player.position += self.player.direction * (PLAYER_SPEED * 15 * self.data.get('shop', {}).get('player_speed', 0))

    def spawn_bullet(self, direction):
        bullet = Bullet(INVENTORY_ITEMS[self.inventory.current_inventory_item][3], getattr(utils.preload, INVENTORY_ITEMS[self.inventory.current_inventory_item][4]), self.player.center_x, self.player.center_y, direction)
        bullet.speed = BULLET_SPEED + self.data.get('shop', {}).get("bullet_speed", 0)
        self.bullets.append(bullet)
        self.spritelist.append(bullet)

    def get_current_level_int(self):
        return TAX_EVASION_NAMES.index(self.tax_evasion_level)

    def update_evasion_level(self):
        before = self.get_current_level_int()

        if self.evaded_tax <= 0:
            self.tax_evasion_level = TAX_EVASION_NAMES[0]
        else:
            for tax_evasion_level, tax_evasion_min in TAX_EVASION_LEVELS.items():
                if self.evaded_tax >= tax_evasion_min:
                    self.tax_evasion_level = tax_evasion_level

        if before < self.get_current_level_int():
            self.tax_evasion_level_notice.text = f"Tax Evasion Level Increased to {self.tax_evasion_level}"
            self.tax_evasion_level_notice.visible = True
            self.last_tax_evasion_notice = time.perf_counter()
        elif before > self.get_current_level_int():
            self.tax_evasion_level_notice.text = f"Tax Evasion Level Decreased to {self.tax_evasion_level}"
            self.tax_evasion_level_notice.visible = True
            self.last_tax_evasion_notice = time.perf_counter()

        if not self.evaded_tax < 0:
            if not self.get_current_level_int() == len(TAX_EVASION_NAMES) - 1:
                self.progress_bar.value = ((self.evaded_tax - TAX_EVASION_LEVELS[self.tax_evasion_level]) / (TAX_EVASION_LEVELS[TAX_EVASION_NAMES[self.get_current_level_int() + 1]] - TAX_EVASION_LEVELS[self.tax_evasion_level])) * 100
            else:
                self.progress_bar.value = 100
        else:
            self.progress_bar.value = 0

        self.tax_evasion_label.text = f"Tax Evasion Level: {self.tax_evasion_level}"

    def pay_tax(self):
        if self.evaded_tax >= 1000:
            self.evaded_tax -= 1000
            self.update_evasion_level()

    def spawn_irs_agent(self):
        base_x = self.window.width / 2
        base_y = self.window.height / 2
        amount = self.window.width / 3

        angle = random.randint(0, 361)

        x = base_x + (math.cos(angle) * amount)
        y = base_y + (math.sin(angle) * amount)

        irs_agent = IRSAgent(x, y)
        irs_agent.health = IRS_AGENT_HEALTH + (HEALTH_INCREASE_PER_LEVEL * self.get_current_level_int())

        self.irs_agents.append(irs_agent)
        self.spritelist.append(irs_agent)

    def on_update(self, delta_time):
        self.player.update_animation()

        if self.window.keyboard[arcade.key.W]:
            self.player.direction = arcade.math.Vec2(self.player.direction.x, 1)
            if not self.player.animation == (dark_wizard_up_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_up_animation): # this is needed because the animation property will reset to the first frame, so animation doesnt work.
                self.player.animation = (dark_wizard_up_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_up_animation)
        elif self.window.keyboard[arcade.key.S]:
            self.player.direction = arcade.math.Vec2(self.player.direction.x, -1)
            if not self.player.animation == (dark_wizard_standing_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_standing_animation): # this is needed because the animation property will reset to the first frame, so animation doesnt work.
                self.player.animation = (dark_wizard_standing_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_standing_animation)
        else:
            self.player.direction = arcade.math.Vec2(self.player.direction.x, 0)

        if self.window.keyboard[arcade.key.D]:
            self.player.direction = arcade.math.Vec2(1, self.player.direction.y)
            if not self.player.animation == (dark_wizard_right_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_right_animation): # this is needed because the animation property will reset to the first frame, so animation doesnt work.
                self.player.animation = (dark_wizard_right_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_right_animation)
        elif self.window.keyboard[arcade.key.A]:
            self.player.direction = arcade.math.Vec2(-1, self.player.direction.y)
            if not self.player.animation == (dark_wizard_left_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_left_animation): # this is needed because the animation property will reset to the first frame, so animation doesnt work.
                self.player.animation = (dark_wizard_left_animation if self.data["shop"]["dark_mode_wizard"] else light_wizard_left_animation)
        else:
            self.player.direction = arcade.math.Vec2(0, self.player.direction.y)

        self.player.position += self.player.direction * (PLAYER_SPEED + self.data.get('shop', {}).get('player_speed', 0))

        if self.player.center_x + self.player.width / 2 > self.window.width:
            self.player.center_x = self.window.width - self.player.width / 2
        elif self.player.center_x - self.player.width / 2 < 0:
            self.player.center_x = self.player.width / 2

        if self.player.center_y + self.player.height / 2 > self.window.height:
            self.player.center_y = self.window.height - self.player.height / 2
        elif self.player.center_y - self.player.height / 2 < 0:
            self.player.center_y = self.player.height / 2

        item_list = INVENTORY_ITEMS[self.inventory.current_inventory_item]

        json_name = item_to_json_name[item_list[0]]

        if time.perf_counter() - self.last_shoot >= item_list[1] - ((item_list[1] / 15) * self.data["shop"][f"{json_name}_atk_speed"]):
            self.last_shoot = time.perf_counter()
            
            mouse_pos = arcade.math.Vec2(
                self.window.mouse.data.get("x", 0),
                self.window.mouse.data.get("y", 0)
            )

            player_pos = arcade.math.Vec2(self.player.center_x, self.player.center_y)

            direction = (mouse_pos - player_pos).normalize()

            inaccuracy = random.randint(-(PLAYER_INACCURACY_MAX - self.data["shop"]["inaccuracy_decrease"]), (PLAYER_INACCURACY_MAX - self.data["shop"]["inaccuracy_decrease"]))
            self.spawn_bullet(direction.rotate(math.radians(inaccuracy)))

        if self.tax_evasion_level_notice.visible and time.perf_counter() - self.last_tax_evasion_notice >= 2.5:
            self.tax_evasion_level_notice.visible = False

        if time.perf_counter() - self.last_mana >= 0.5:
            self.last_mana = time.perf_counter()
            
            self.mana += 5
            
            self.mana_label.text = f"Mana: {self.mana}"

        self.camera_shake.update(delta_time)

        for irs_agent in self.irs_agents:
            irs_agent.update()

            wizard_pos_vec = arcade.math.Vec2(self.player.center_x, self.player.center_y)

            if wizard_pos_vec.distance(irs_agent.position) <= self.player.width / 2:
                if time.perf_counter() - irs_agent.last_attack >= IRS_AGENT_ATTACK_SPEED:
                    irs_agent.last_attack = time.perf_counter()

                    self.camera_shake.start()
                    
                    self.evaded_tax -= TAX_PER_IRS_AGENT + (TAX_INCREASE_PER_LEVEL * self.get_current_level_int())
                    self.update_evasion_level()
            else:
                direction = (wizard_pos_vec - irs_agent.position).normalize()
                irs_agent.angle = -math.degrees(direction.heading())
                irs_agent.position += direction * (IRS_AGENT_SPEED + (SPEED_INCREASE_PER_LEVEL * self.get_current_level_int()))

        for bullet in self.bullets:
            bullet.move()

            hit = False

            for irs_agent in self.irs_agents:
                if arcade.math.Vec2(bullet.center_x, bullet.center_y).distance((irs_agent.center_x, irs_agent.center_y)) <= (irs_agent.width / 2 + bullet.radius):
                    irs_agent.damaged = True
                    irs_agent.last_damage = time.perf_counter()
                    
                    damage = item_list[2] + (item_list[2] / 10 * self.data["shop"][f"{json_name}_dmg"])

                    irs_agent.position += bullet.direction * damage * 1.5
                    irs_agent.health -= damage

                    if irs_agent.health <= 0:
                        self.spritelist.remove(irs_agent)
                        self.irs_agents.remove(irs_agent)
                        self.evaded_tax += (TAX_PER_IRS_AGENT / 2) + ((TAX_INCREASE_PER_LEVEL / 2) * self.get_current_level_int())
                        self.update_evasion_level()

                    self.camera_shake.start()
                    hit = True

            if hit:
                self.spritelist.remove(bullet)
                self.bullets.remove(bullet)

        if time.perf_counter() - self.last_irs_agent_spawn >= IRS_AGENT_SPAWN_INTERVAL - (SPAWN_INTERVAL_DECREASE_PER_LEVEL * self.get_current_level_int()):
            self.last_irs_agent_spawn = time.perf_counter()

            self.spawn_irs_agent()

        if self.evaded_tax >= 0:
            self.evaded_tax_label.text = f"Evaded Tax: {int(self.evaded_tax)}$"
        else:
            self.evaded_tax_label.text = f"Tax Debt: {int(abs(self.evaded_tax))}$"

        if self.evaded_tax > self.high_score:
            self.high_score = self.evaded_tax
            self.high_score_label.text = f"High Score: {int(self.high_score)}$"

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.data["high_score"] = int(self.high_score)
            self.data["evaded_tax"] += int(self.evaded_tax)
            with open("data.json", "w") as file:
                file.write(json.dumps(self.data, indent=4))

            arcade.set_background_color(menu_background_color)

            from menus.main import Main
            self.window.show_view(Main(self.pypresence_client))
        elif symbol in INVENTORY_TRIGGER_KEYS:
            self.inventory.select_item(int(chr(symbol)) - 1)
        elif symbol == arcade.key.P:
            self.pay_tax()
        elif symbol == arcade.key.TAB:
            self.dash()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera.match_window()

    def on_draw(self):
        self.window.clear()

        self.camera_shake.update_camera()
        self.camera.use()
        self.spritelist.draw()
        self.camera_shake.readjust_camera()

        self.ui.draw() # draw after, so UI is on top