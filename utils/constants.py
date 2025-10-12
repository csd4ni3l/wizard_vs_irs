import arcade.color, arcade.key
from arcade.types import Color
from arcade.gui.widgets.buttons import UITextureButtonStyle, UIFlatButtonStyle
from arcade.gui.widgets.slider import UISliderStyle

menu_background_color = (30, 30, 47)
log_dir = 'logs'
discord_presence_id = 1424784736726945915

IRS_AGENT_SPAWN_INTERVAL = 0.8

IRS_AGENT_TYPES = [
    (1, 2.25, 15, 200), # Normal
    (0.9, 3.5, 8, 150), # Speedrunner
    (1.3, 1.5, 35, 350) # Auditor
]

SPEED_INCREASE_PER_LEVEL = 1 / 5
SPAWN_INTERVAL_DECREASE_PER_LEVEL = 1 / 20
HEALTH_INCREASE_PER_LEVEL = 1 / 7.5
TAX_INCREASE_PER_LEVEL = 1 / 3
ATTACK_INTERVAL_DECREASE_PER_LEVEL = 1 / 10

TAX_EVASION_LEVELS = {
    "Compliant Citizen": 0,
    "Minor Mistake": 1000,            
    "Mildly Suspicious": 2500,
    "Suspicious": 5000,
    "Under Review": 7500,
    "Investigated": 10000,
    "Flagged": 13500,
    "Audited": 25000,
    "Seized Assets": 40000,
    "Criminal Case": 70000,
    "International Watchlist": 125000,
    "Most Wanted": 250000,
    "Legendary": 500000,
    "THE ONE AND ONLY TAX EVADER": 1000000
}
TAX_EVASION_NAMES = list(TAX_EVASION_LEVELS.keys())

BULLET_SPEED = 8
PLAYER_INACCURACY_MAX = 10
PLAYER_SPEED = 4

# name, json_key, max_count, upgrade_cost
SHOP_ITEMS = [
    ["Fireball DMG", "fb_dmg", 999, 10000],
    ["Fireball ATK Speed", "fb_atk_speed", 10, 30000],
    ["Ball of Lightning DMG", "lb_dmg", 999, 10000],
    ["Ball of Lightning ATK Speed", "lb_atk_speed", 10, 30000],
    ["Ice Blast DMG", "ib_dmg", 999, 10000],
    ["Ice Blast ATK Speed", "ib_atk_speed", 10, 30000],
    ["Inaccuracy Decrease", "inaccuracy_decrease", 10, 25000],
    ["Player Speed", "player_speed", 15, 20000],
    ["Bullet Speed", "bullet_speed", 999, 20000],
    ["Dark Mode Wizard", "dark_mode_wizard", 1, 1000000]
]

INVENTORY_ITEMS = [
    ["Fireball", 0.25, 10, 10, "fireball_texture"],
    ["Ball of Lightning", 0.45, 20, 20, "lightning_bolt_texture"],
    ["Ice Blast", 0.15, 5, 7.5, "ice_blast_texture"],
]

ABILITIES = {
    "dash": 20,
    "tax_shield": 50,
    "audit_bomb": 100,
    "freeze_audit": 150
}

item_to_json_name = {
    "Fireball": "fb",
    "Ball of Lightning": "bl",
    "Ice Blast": "ib"
}

INVENTORY_TRIGGER_KEYS = [getattr(arcade.key, f"KEY_{n+1}") for n in range(len(INVENTORY_ITEMS))]

button_style = {'normal': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK), 'hover': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK),
                'press': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK), 'disabled': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK)}
big_button_style = {'normal': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, font_size=26), 'hover': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, font_size=26),
                'press': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, font_size=26), 'disabled': UITextureButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, font_size=26)}

dropdown_style = {'normal': UIFlatButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, bg=Color(128, 128, 128)), 'hover': UIFlatButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, bg=Color(49, 154, 54)),
                  'press': UIFlatButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, bg=Color(128, 128, 128)), 'disabled': UIFlatButtonStyle(font_name="Roboto", font_color=arcade.color.BLACK, bg=Color(128, 128, 128))}

slider_default_style = UISliderStyle(bg=Color(128, 128, 128), unfilled_track=Color(128, 128, 128), filled_track=Color(49, 154, 54))
slider_hover_style = UISliderStyle(bg=Color(49, 154, 54), unfilled_track=Color(128, 128, 128), filled_track=Color(49, 154, 54))

slider_style = {'normal': slider_default_style, 'hover': slider_hover_style, 'press': slider_hover_style, 'disabled': slider_default_style}

settings = {
    "Graphics": {
        "Window Mode": {"type": "option", "options": ["Windowed", "Fullscreen", "Borderless"], "config_key": "window_mode", "default": "Windowed"},
        "Resolution": {"type": "option", "options": ["1366x768", "1440x900", "1600x900", "1920x1080", "2560x1440", "3840x2160"], "config_key": "resolution"},
        "Anti-Aliasing": {"type": "option", "options": ["None", "2x MSAA", "4x MSAA", "8x MSAA", "16x MSAA"], "config_key": "anti_aliasing", "default": "4x MSAA"},
        "VSync": {"type": "bool", "config_key": "vsync", "default": True},
        "FPS Limit": {"type": "slider", "min": 0, "max": 480, "config_key": "fps_limit", "default": 60},
    },
    "Sound": {
        "Music": {"type": "bool", "config_key": "music", "default": True},
        "SFX": {"type": "bool", "config_key": "sfx", "default": True},
        "Music Volume": {"type": "slider", "min": 0, "max": 100, "config_key": "music_volume", "default": 50},
        "SFX Volume": {"type": "slider", "min": 0, "max": 100, "config_key": "sfx_volume", "default": 50},
    },
    "Miscellaneous": {
        "Discord RPC": {"type": "bool", "config_key": "discord_rpc", "default": True},
    },
    "Credits": {}
}
settings_start_category = "Graphics"
