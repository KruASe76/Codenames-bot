from pathlib import Path

from PIL import ImageFont
from discord import Color


EMPTY = "\u2063"  # invisible separator

ADMINS = {689766059712315414, 790535470870298642, 783324731364737034}

LOGO_LINK = "https://codenames.me/favicon/apple-touch-icon-144x144.png"

ALPHABET = "ABCDEFGHIJKLMNOPQSTUVWXYZ"  # Without letter R
REACTION_ALPHABET = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇸🇹🇺🇻🇼🇽🇾🇿"  # Without R too
REACTION_R = "🇷"
REACTION_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣")


font = ImageFont.truetype(str(Path("resources", "fonts", "RobotoCondensed-Bold.ttf")), 80, encoding="utf-8")
big_font = ImageFont.truetype(str(Path("resources", "fonts", "Roboto-Bold.ttf")), 350, encoding="utf-8")


dictionaries = {
    "en": {
        "std":      "**Original** English dictionary (400 words)",
        "duet":     "**Original Duet** dictionary (400 words)",
        "deep":     "**Original Deep Undercover** dictionary (**18+**, 390 words)",
        "denull":   "**deNULL's** dictionary (763 words)",
        "denull18": "**deNULL's** dictionary (**18+**, 1081 words)",
        "all":      "**All** English dictionaries (**18+**, 1139 words)",
        "esp":      "**Esperanto**"
    },
    "ru": {
        "std":      "**Стандартный** словарь из локализации GaGa Games (400 слов)",
        "deep":     "Словарь версии **Deep Undercover**, GaGa Games (**18+**, 390 слов)",
        "pard":     "Словарь от **Pard** (302 слова)",
        "vpupkin":  "Словарь от **vpupkin** (396 слов, много топонимов)",
        "zav":      "Словарь от **Ивана Заворина** (2272 частых слов)",
        "denull":   "Словарь от **deNULL** (636 слов, немного топонимов)",
        "denull18": "Словарь от **deNULL** (**18+**, 1014 слов)",
        "all":      "**Все** словари **вместе** (**18+**, 1058 слов)",
        "esp":      "**Esperanto**"
    }
}

flags_loc = {
    "en": "🇬🇧",
    "ru": "🇷🇺"
}
flags_loc_rev = {v: k for k, v in flags_loc.items()}

flags_lang = {
    "en": "🇬🇧",
    "ru": "🇷🇺"
}
flags_lang_rev = {v: k for k, v in flags_lang.items()}


class Paths:
    img_dir = Path("state", "images")
    db = Path("state", "base.db")

    @classmethod
    def cap_img(cls, uuid: str) -> Path:
        return Path(cls.img_dir, f"{uuid}-captain.png")

    @classmethod
    def cap_img_init(cls, uuid: str) -> Path:
        return Path(cls.img_dir, f"{uuid}-captain-initial.png")

    @classmethod
    def pl_img(cls, uuid: str) -> Path:
        return Path(cls.img_dir, f"{uuid}-player.png")

    @staticmethod
    def dictionary(language: str, name: str) -> Path:
        return Path("resources", "dictionaries", language, f"{name}.txt")


class FieldSizing:
    width = 3840
    height = 2160

    text_anchor = "mm"  # Middle of the rectangle

    footer_height = 400

    card_count = 5
    card_spacing = 50
    card_width = (width - (card_spacing * (card_count + 1))) / card_count
    card_height = (height - footer_height - (card_spacing * (card_count + 1))) / card_count
    card_radius = 10
    card_outline_width = 2


class Colors:
    purple = Color.from_rgb(141, 8, 210)
    red = Color.from_rgb(255, 100, 80)
    blue = Color.from_rgb(80, 187, 255)
    white = Color.from_rgb(220, 220, 220)
    black = Color.from_rgb(34, 34, 34)

    red_fill = (255, 100, 80)
    red_font = (136, 16, 0)
    red_opened_fill = (255, 223, 219)
    red_opened_font = red_font

    blue_fill = (80, 187, 255)
    blue_font = (0, 84, 138)
    blue_opened_fill = (219, 241, 255)
    blue_opened_font = blue_font

    black_fill = (68, 68, 68)
    black_font = (170, 170, 170)
    black_opened_fill = (217, 217, 217)
    black_opened_font = black_font

    white_fill = (250, 250, 250)
    white_outline = (220, 220, 220)
    white_font = (68, 68, 68)
    white_opened_cap_fill = (253, 253, 253)
    white_opened_cap_outline = (248, 248, 248)
    white_opened_cap_font = (217, 217, 217)
    white_opened_pl_fill = (255, 252, 245)
    white_opened_pl_outline = white_opened_pl_fill
    white_opened_pl_font = (216, 207, 173)
