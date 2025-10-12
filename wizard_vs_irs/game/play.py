import arcade, arcade.gui, random, math, time, json, math

from wizard_vs_irs.utils.constants import (
    ABILITIES,
    ATTACK_INTERVAL_DECREASE_PER_LEVEL,
    BULLET_SPEED,
    HEALTH_INCREASE_PER_LEVEL,
    INVENTORY_ITEMS,
    INVENTORY_TRIGGER_KEYS,
    IRS_AGENT_SPAWN_INTERVAL,
    IRS_AGENT_TYPES,
    item_to_json_name,  # if it's a variable, better to keep original case
    PLAYER_INACCURACY_MAX,
    PLAYER_SPEED,
    SPAWN_INTERVAL_DECREASE_PER_LEVEL,
    SPEED_INCREASE_PER_LEVEL,
    TAX_EVASION_LEVELS,
    TAX_EVASION_NAMES,
    TAX_INCREASE_PER_LEVEL,
)

import wizard_vs_irs.utils.preload
from wizard_vs_irs.utils.preload import irs_agent_texture
from wizard_vs_irs.utils.preload import light_wizard_left_animation, light_wizard_right_animation, light_wizard_standing_animation, light_wizard_up_animation
from wizard_vs_irs.utils.preload import dark_wizard_left_animation, dark_wizard_right_animation, dark_wizard_standing_animation, dark_wizard_up_animation

from wizard_vs_irs.game.inventory import Inventory

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

        self.speed, self.attack_speed, self.health, self.tax = 0, 0, 0, 0

        self.damaged = False
        self.last_damage = time.perf_counter()
        self.last_attack = time.perf_counter()

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

    def set_player_animation(self, animation):  # this is needed because the animation property will reset to the first frame, so animation doesnt work.
        self.animation = animation

class DamageNumberLabel(arcade.gui.UILabel):
    def __init__(self, x, y, damage):
        super().__init__(x=x, y=y, text=f"-{int(damage)}", text_color=arcade.color.RED)

        self.original_y = y
        self.finished = False

    def update(self):
        if self.center_y - self.original_y < 50:
            self.rect = self.rect.move(0, 2)
        else:
            self.finished = True

class Game(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

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
        self.damage_numbers: list[arcade.gui.UILabel] = []
        self.last_irs_agent_spawn = time.perf_counter()
        self.last_mana = time.perf_counter()
        self.last_shoot = time.perf_counter()

        self.evaded_tax = 0
        self.high_score = self.data["high_score"]
        self.mana = 0
        self.tax_evasion_level = TAX_EVASION_NAMES[0]

        self.tax_shield = 0
        self.immobilize_irs = False
        self.last_immobilization = time.perf_counter()
        self.last_ability_timers = {}

        self.bullets: list[Bullet] = []
        self.player = Player(self.window.width / 2, self.window.height / 2, self.data["shop"].get("dark_mode_wizard", 0))
        self.spritelist.append(self.player)

        self.info_box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=0, align="left"), anchor_x="left", anchor_y="top")
        self.evaded_tax_label = self.info_box.add(arcade.gui.UILabel(text="Evaded Tax: 0$", font_size=14))
        self.high_score_label = self.info_box.add(arcade.gui.UILabel(text=f"High Score: {self.high_score}$", font_size=14))
        self.mana_label = self.info_box.add(arcade.gui.UILabel(text="Mana: 0", font_size=14))
        self.tax_evasion_label = self.info_box.add(arcade.gui.UILabel(text=f"Tax Evasion Level: {self.tax_evasion_level}", font_size=14))
        
        self.tax_evasion_level_notice = self.anchor.add(arcade.gui.UILabel(text="Tax Evasion Level Increased to example", font_size=28), anchor_x="center", anchor_y="top")
        self.tax_evasion_level_notice.visible = False
        self.last_tax_evasion_notice = time.perf_counter()

        self.progress_bar = self.anchor.add(arcade.gui.UISlider(value=0, max_value=100, size_hint=(0.5, 0.15)), anchor_x="center", anchor_y="top")
        self.progress_bar._render_steps = lambda surface: None
        self.progress_bar._render_thumb = lambda surface: None
        self.progress_bar.on_event = lambda event: None

        self.ability_info_label = self.anchor.add(arcade.gui.UILabel(text=f"""Abilities:
Dash (tab): {ABILITIES['dash']} Mana
Tax Shield (t): {ABILITIES["tax_shield"]} Mana
Audit Bomb (b): {ABILITIES["audit_bomb"]} Mana
Freeze Audit (f): {ABILITIES["freeze_audit"]} Mana""", font_size=20, multiline=True), 
anchor_x="right", anchor_y="bottom", align_x=-5)

        self.inventory = self.anchor.add(Inventory(INVENTORY_ITEMS, self.window.width), anchor_x="left", anchor_y="bottom", align_x=self.window.width / 20)
        self.inventory.pay_tax_button.on_click = lambda event: self.pay_tax()

    def damage_irs_agent(self, irs_agent):
        irs_agent.damaged = True
        irs_agent.last_damage = time.perf_counter()
        
        item_list = INVENTORY_ITEMS[self.inventory.current_inventory_item]

        json_name = item_to_json_name[item_list[0]]

        damage = item_list[2] + (item_list[2] / 10 * self.data["shop"].get(f"{json_name}_dmg", 0))

        irs_agent.health -= damage

        self.damage_numbers.append(self.ui.add(DamageNumberLabel(irs_agent.left, irs_agent.top, damage)))

        if irs_agent.health <= 0:
            self.spritelist.remove(irs_agent)
            self.irs_agents.remove(irs_agent)
            self.evaded_tax += irs_agent.tax / 2
            self.update_evasion_level()

        self.camera_shake.start()

    def ability(self, ability):
        if self.mana >= ABILITIES[ability]:
            self.mana -= ABILITIES[ability]
            self.last_ability_timers[ability] = time.perf_counter()

            if ability == "dash":
                self.player.position += self.player.direction * (PLAYER_SPEED + self.data.get('shop', {}).get('player_speed', 0)) * 30
            elif ability == "tax_shield":
                self.tax_shield += 750
            elif ability == "audit_bomb":
                for irs_agent in self.irs_agents:
                    if arcade.math.Vec2(self.player.center_x, self.player.center_y).distance((irs_agent.center_x, irs_agent.center_y)) <= 250:
                        for i in range(3):
                            if irs_agent in self.irs_agents: # if they died the first or second time, they cant be damaged again
                                self.damage_irs_agent(irs_agent)
            elif ability == "freeze_audit":
                self.last_immobilization = time.perf_counter()
                self.immobilize_irs = True

    def spawn_bullet(self, direction):
        bullet = Bullet(INVENTORY_ITEMS[self.inventory.current_inventory_item][3], getattr(wizard_vs_irs.utils.preload, INVENTORY_ITEMS[self.inventory.current_inventory_item][4]), self.player.center_x, self.player.center_y, direction)
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
        atk_speed, speed, health, tax = random.choice(IRS_AGENT_TYPES)

        agent = IRSAgent(x, y)
        agent.attack_speed = atk_speed - (ATTACK_INTERVAL_DECREASE_PER_LEVEL * self.get_current_level_int())
        agent.speed = speed + (SPEED_INCREASE_PER_LEVEL * self.get_current_level_int())
        agent.health = health + (HEALTH_INCREASE_PER_LEVEL * self.get_current_level_int())
        agent.tax = tax + (TAX_INCREASE_PER_LEVEL * self.get_current_level_int())
        
        self.irs_agents.append(agent)
        self.spritelist.append(agent)

    def on_update(self, delta_time):
        if self.immobilize_irs and time.perf_counter() - self.last_immobilization >= 4:
            self.immobilize_irs = False

        for damage_number_label in self.damage_numbers:
            damage_number_label.update()

            if damage_number_label.finished:
                self.damage_numbers.remove(damage_number_label)
                self.ui.remove(damage_number_label)
                
        self.camera_shake.update(delta_time)
        self.player.update_animation()

        if self.window.keyboard[arcade.key.W]:
            self.player.direction = arcade.math.Vec2(self.player.direction.x, 1)
            self.player.set_player_animation(dark_wizard_up_animation if self.data["shop"].get("dark_mode_wizard", False) else light_wizard_up_animation)
        elif self.window.keyboard[arcade.key.S]:
            self.player.direction = arcade.math.Vec2(self.player.direction.x, -1)
            self.player.set_player_animation(dark_wizard_standing_animation if self.data["shop"].get("dark_mode_wizard", False) else light_wizard_standing_animation)
        else:
            self.player.direction = arcade.math.Vec2(self.player.direction.x, 0)

        if self.window.keyboard[arcade.key.D]:
            self.player.direction = arcade.math.Vec2(1, self.player.direction.y)
            self.player.set_player_animation(dark_wizard_right_animation if self.data["shop"].get("dark_mode_wizard", False) else light_wizard_right_animation)
        elif self.window.keyboard[arcade.key.A]:
            self.player.direction = arcade.math.Vec2(-1, self.player.direction.y)
            self.player.set_player_animation(dark_wizard_left_animation if self.data["shop"].get("dark_mode_wizard", False) else light_wizard_left_animation)
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

        if time.perf_counter() - self.last_shoot >= item_list[1] - ((item_list[1] / 15) * self.data["shop"].get(f"{json_name}_atk_speed", 0)):
            self.last_shoot = time.perf_counter()
            
            mouse_pos = arcade.math.Vec2(
                self.window.mouse.data.get("x", 0),
                self.window.mouse.data.get("y", 0)
            )

            player_pos = arcade.math.Vec2(self.player.center_x, self.player.center_y)

            direction = (mouse_pos - player_pos).normalize()

            inaccuracy = random.randint(-(PLAYER_INACCURACY_MAX - self.data["shop"].get("inaccuracy_decrease", 0)), (PLAYER_INACCURACY_MAX - self.data["shop"].get("inaccuracy_decrease", 0)))
            self.spawn_bullet(direction.rotate(math.radians(inaccuracy)))

        if self.tax_evasion_level_notice.visible and time.perf_counter() - self.last_tax_evasion_notice >= 2.5:
            self.tax_evasion_level_notice.visible = False

        if time.perf_counter() - self.last_mana >= 0.5:
            self.last_mana = time.perf_counter()
            
            self.mana += 5
            
            self.mana_label.text = f"Mana: {self.mana}"
        
        if not self.immobilize_irs:
            for irs_agent in self.irs_agents:
                irs_agent.update()

                wizard_pos_vec = arcade.math.Vec2(self.player.center_x, self.player.center_y)

                if wizard_pos_vec.distance(irs_agent.position) <= self.player.width / 2:
                    if time.perf_counter() - irs_agent.last_attack >= irs_agent.attack_speed:
                        irs_agent.last_attack = time.perf_counter()

                        self.camera_shake.start()

                        if not self.tax_shield > 0:
                            self.evaded_tax -= irs_agent.tax
                        else:
                            if irs_agent.tax > self.tax_shield:
                                self.evaded_tax -= irs_agent.tax - self.tax_shield
                                self.tax_shield = 0
                            else:
                                self.tax_shield -= irs_agent.tax

                        self.damage_numbers.append(self.ui.add(DamageNumberLabel(self.player.left, self.player.top, irs_agent.tax)))
        
                        self.update_evasion_level()
                else:
                    direction = (wizard_pos_vec - irs_agent.position).normalize()
                    irs_agent.angle = -math.degrees(direction.heading())
                    irs_agent.position += direction * irs_agent.speed

        for bullet in self.bullets:
            bullet.move()

            hit = False

            for irs_agent in self.irs_agents:
                if arcade.math.Vec2(bullet.center_x, bullet.center_y).distance((irs_agent.center_x, irs_agent.center_y)) <= (irs_agent.width / 2 + bullet.radius):
                    self.damage_irs_agent(irs_agent)
                    damage = item_list[2] + (item_list[2] / 10 * self.data["shop"].get(f"{json_name}_dmg", 0))
                    irs_agent.position += bullet.direction * damage * 1.5
                    hit = True

            if hit or bullet.center_x + bullet.radius / 2 > self.window.width or bullet.center_x - bullet.radius / 2 < 0 or bullet.center_y + bullet.radius / 2 > self.window.height or bullet.center_y - bullet.height / 2 < 0:
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

            from wizard_vs_irs.menus.main import Main
            self.window.show_view(Main(self.pypresence_client))
        elif symbol in INVENTORY_TRIGGER_KEYS:
            self.inventory.select_item(int(chr(symbol)) - 1)
        elif symbol == arcade.key.P:
            self.pay_tax()
        elif symbol == arcade.key.TAB:
            self.ability("dash")
        elif symbol == arcade.key.T:
            self.ability("tax_shield")
        elif symbol == arcade.key.B:
            self.ability("audit_bomb")
        elif symbol == arcade.key.F:
            self.ability("freeze_audit")

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