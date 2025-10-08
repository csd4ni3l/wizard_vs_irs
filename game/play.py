import arcade, arcade.gui, random, math, time, json, os

from utils.constants import BULLET_SPEED, TAX_EVASION_LEVELS, INVENTORY_ITEMS, IRS_AGENT_SPEED, TAX_PER_IRS_AGENT, IRS_AGENT_SPAWN_INTERVAL, SPAWN_INTERVAL_DECREASE_PER_LEVEL, SPEED_INCREASE_PER_LEVEL, TAX_EVASION_NAMES, TAX_INCREASE_PER_LEVEL, menu_background_color
from utils.preload import wizard_texture, irs_agent_texture

from game.inventory import Inventory

class Bullet(arcade.Sprite):
    def __init__(self, x, y, direction, color, **kwargs):
        super().__init__(arcade.texture.make_circle_texture(20, color), center_x=x, center_y=y)
        self.direction = direction

    def move(self):
        self.position += self.direction * BULLET_SPEED

class Game(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

        arcade.set_background_color(arcade.color.WHITE)

        self.pypresence_client = pypresence_client
        self.pypresence_client.update(state="Playing the game")

        if os.path.exists("data.json"):
            with open("data.json", "r") as file:
                self.data = json.load(file)
        else:
            self.data = {
                "high_score": 0
            }

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

        self.irs_agents = []
        self.last_irs_agent_spawn = time.perf_counter()
        self.last_mana = time.perf_counter()

        self.evaded_tax = 0
        self.mana = 0
        self.tax_evasion_level = TAX_EVASION_NAMES[0]

        self.bullets: list[Bullet] = []
        self.highscore_evaded_tax = self.data["high_score"]
        self.wizard_sprite = arcade.Sprite(wizard_texture, center_x=self.window.width / 2, center_y=self.window.height / 2)
        self.spritelist.append(self.wizard_sprite)

        self.info_box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=0, align="left"), anchor_x="left", anchor_y="top")
        self.evaded_tax_label = self.info_box.add(arcade.gui.UILabel(text="Evaded Tax: 0$", font_size=14, text_color=arcade.color.BLACK))
        self.mana_label = self.info_box.add(arcade.gui.UILabel(text="Mana: 0", font_size=14, text_color=arcade.color.BLACK))
        self.tax_evasion_label = self.info_box.add(arcade.gui.UILabel(text=f"Tax Evasion Level: {self.tax_evasion_level}", font_size=14, text_color=arcade.color.BLACK))
        
        self.tax_evasion_level_notice = self.anchor.add(arcade.gui.UILabel(text="Tax Evasion Level Increased to example", font_size=28, text_color=arcade.color.BLACK), anchor_x="center", anchor_y="top")
        self.tax_evasion_level_notice.visible = False
        self.last_tax_evasion_notice = time.perf_counter()

        self.progress_bar = self.anchor.add(arcade.gui.UISlider(value=0, max_value=100, size_hint=(0.5, 0.15)), anchor_x="center", anchor_y="top")
        self.progress_bar._render_steps = lambda surface: None
        self.progress_bar._render_thumb = lambda surface: None
        self.progress_bar.on_event = lambda event: None

        self.inventory = self.anchor.add(Inventory(INVENTORY_ITEMS, self.window.width), anchor_x="center", anchor_y="bottom")
        self.inventory.pay_tax_button.on_click = lambda event: self.pay_tax()

    def spawn_bullet(self, direction):
        bullet = Bullet(self.window.width / 2, self.window.height / 2, direction, arcade.color.BLUE)
        self.bullets.append(bullet)
        self.spritelist.append(bullet)

    def auto_shoot(self):
        closest_dist = 999999
        closest_direction = None

        for irs_agent in self.irs_agents:
            distance = arcade.math.Vec2(self.wizard_sprite.center_x, self.wizard_sprite.center_y).distance((irs_agent.center_x, irs_agent.center_y))

            if distance < closest_dist:
                closest_dist = distance
                closest_direction = (arcade.math.Vec2(irs_agent.center_x, irs_agent.center_y) - (self.wizard_sprite.center_x, self.wizard_sprite.center_y)).normalize()

        if not closest_dist or not closest_direction:
            return
        
        self.spawn_bullet(closest_direction)

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

        self.progress_bar.value = ((self.evaded_tax - TAX_EVASION_LEVELS[self.tax_evasion_level]) / (TAX_EVASION_LEVELS[TAX_EVASION_NAMES[self.get_current_level_int() + 1]] - TAX_EVASION_LEVELS[self.tax_evasion_level])) * 100

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

        irs_agent = arcade.Sprite(irs_agent_texture, center_x=x, center_y=y)

        self.irs_agents.append(irs_agent)
        self.spritelist.append(irs_agent)

    def on_update(self, delta_time):
        if self.tax_evasion_level_notice.visible and time.perf_counter() - self.last_tax_evasion_notice >= 2.5:
            self.tax_evasion_level_notice.visible = False

        if time.perf_counter() - self.last_mana >= 0.1:
            self.last_mana = time.perf_counter()
            
            self.mana += 5
            
            self.mana_label.text = f"Mana: {self.mana}"

        self.camera_shake.update(delta_time)

        for irs_agent in self.irs_agents:
            wizard_pos_vec = arcade.math.Vec2(self.wizard_sprite.center_x, self.wizard_sprite.center_y)
            direction = (wizard_pos_vec - irs_agent.position).normalize()

            irs_agent.position += direction * (IRS_AGENT_SPEED + (SPEED_INCREASE_PER_LEVEL * self.get_current_level_int()))

            if wizard_pos_vec.distance(irs_agent.position) <= self.wizard_sprite.width / 2:
                self.camera_shake.start()
                
                self.evaded_tax -= TAX_PER_IRS_AGENT + (TAX_INCREASE_PER_LEVEL * self.get_current_level_int())
                self.update_evasion_level()

                self.spritelist.remove(irs_agent)
                self.irs_agents.remove(irs_agent)
        
        for bullet in self.bullets:
            bullet.move()

            hit = False

            for irs_agent in self.irs_agents:
                if arcade.math.Vec2(bullet.center_x, bullet.center_y).distance((irs_agent.center_x, irs_agent.center_y)) <= irs_agent.width:
                    self.spritelist.remove(irs_agent)
                    self.irs_agents.remove(irs_agent)
                    hit = True

                    break

            if hit:
                self.spritelist.remove(bullet)
                self.bullets.remove(bullet)

                self.camera_shake.start()

                self.evaded_tax += 100
                self.update_evasion_level()

        if time.perf_counter() - self.last_irs_agent_spawn >= IRS_AGENT_SPAWN_INTERVAL - (SPAWN_INTERVAL_DECREASE_PER_LEVEL * self.get_current_level_int()):
            self.last_irs_agent_spawn = time.perf_counter()

            self.spawn_irs_agent()

        if self.evaded_tax >= 0:
            self.evaded_tax_label.text = f"Evaded Tax: {self.evaded_tax}$"
        else:
            self.evaded_tax_label.text = f"Tax Debt: {abs(self.evaded_tax)}$"

    def on_show_view(self):
        super().on_show_view()

    def on_mouse_press(self, x, y, button, modifiers):
        direction = ((x, y) - arcade.math.Vec2(self.wizard_sprite.center_x, self.wizard_sprite.center_y)).normalize()

        self.spawn_bullet(direction)

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            arcade.set_background_color(menu_background_color)

            from menus.main import Main
            self.window.show_view(Main(self.pypresence_client))
        elif chr(symbol).isnumeric() and int(chr(symbol)) <= len(INVENTORY_ITEMS):
            self.inventory.select_item(int(chr(symbol)) - 1)
        elif symbol == arcade.key.P:
            self.pay_tax()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera.match_window()

    def on_draw(self):
        super().on_draw()
        self.camera_shake.update_camera()
        self.camera.use()
        self.spritelist.draw()
        self.camera_shake.readjust_camera()