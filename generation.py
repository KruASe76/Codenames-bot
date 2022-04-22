from PIL import Image, ImageDraw, ImageFont
import random, os

# Classes with constants
class UltraHD():
    def __init__(self):
        self.x = 3840
        self.y = 2160

class Colors():
    def __init__(self, dark:bool = False):
        self.red_fill = (255, 100, 80)
        self.red_font = (136, 16, 0)
        self.red_opened_fill = (255, 223, 219)
        self.red_opened_font = self.red_font

        self.blue_fill = (80, 187, 255)
        self.blue_font = (0, 84, 138)
        self.blue_opened_fill = (219, 241, 255)
        self.blue_opened_font = self.blue_font

        self.black_fill = (68, 68, 68)
        self.black_font = (170, 170, 170)
        self.black_opened_fill = (217, 217, 217)
        self.black_opened_font = self.black_font

        self.white_fill = (250, 250, 250)
        self.white_outline = (220, 220, 220)
        self.white_font = (68, 68, 68)
        self.white_opened_cap_fill = (253, 253, 253)
        self.white_opened_cap_outline = (248, 248, 248)
        self.white_opened_cap_font = (217, 217, 217)
        self.white_opened_pl_fill = (255, 252, 245)
        self.white_opened_pl_outline = self.white_opened_pl_fill
        self.white_opened_pl_font = (216, 207, 173)

# Useful function
def multiple_choice(seq, count, return_seq=False): # non-repeatable
    seq_type = type(seq)
    seq = list(seq)
    result = []
    for _ in range(count):
        result.append(random.choice(seq))
        seq.remove(result[-1])

    if return_seq:
        return result, seq_type(seq)
    else:
        return result

# Module functions
def field(uhd, col, team1_words, team2_words, endgame_word, other_words, opened_words, order):
    img = Image.new('RGB', (uhd.x, uhd.y), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(os.path.join('fonts', 'RobotoCondensed-Bold.ttf'), 80, encoding='utf-8')
    big_font = ImageFont.truetype(os.path.join('fonts', 'Roboto-Bold.ttf'), 350, encoding='utf-8')

    # Drawing two bottom rectangles with left words counter
    draw.rectangle(
        xy = (0, uhd.y-400, uhd.x/2-1, uhd.y-1),
        fill = col.red_fill,
    )
    red_words_left = 0
    for word in team1_words:
        if word not in opened_words: red_words_left += 1
    draw.text(
        xy = (
            uhd.x/4,
            uhd.y-200
        ),
        text = str(red_words_left),
        fill = col.red_font,
        font = big_font,
        anchor = 'mm'
    )
    draw.rectangle(
        xy = (uhd.x/2, uhd.y-400, uhd.x-1, uhd.y-1),
        fill = col.blue_fill,
    )
    blue_words_left = 0
    for word in team2_words:
        if word not in opened_words: blue_words_left += 1
    draw.text(
        xy = (
            uhd.x * (3/4),
            uhd.y-200
        ),
        text = str(blue_words_left),
        fill = col.blue_font,
        font = big_font,
        anchor = 'mm'
    )

    # Creating two seperate images for two fields
    cap_img = img.copy()
    cap_draw = ImageDraw.Draw(cap_img)
    pl_img = img.copy()
    pl_draw = ImageDraw.Draw(pl_img)
    
    # Filling the captain's field
    for x in range(5):
        for y in range(5):
            word = order[x*5 + y]
            if word in team1_words:
                if word in opened_words:
                    fill_col = col.red_opened_fill
                    outline_col = col.red_opened_fill
                    font_col = col.red_opened_font
                else:
                    fill_col = col.red_fill
                    outline_col = col.red_fill
                    font_col = col.red_font
            elif word in team2_words:
                if word in opened_words:
                    fill_col = col.blue_opened_fill
                    outline_col = col.blue_opened_fill
                    font_col = col.blue_opened_font
                else:
                    fill_col = col.blue_fill
                    outline_col = col.blue_fill
                    font_col = col.blue_font
            elif word == endgame_word:
                if word in opened_words:
                    fill_col = col.black_opened_fill
                    outline_col = col.black_opened_fill
                    font_col = col.black_opened_font
                else:
                    fill_col = col.black_fill
                    outline_col = col.black_fill
                    font_col = col.black_font
            elif word in other_words:
                if word in opened_words:
                    fill_col = col.white_opened_cap_fill
                    outline_col = col.white_opened_cap_outline
                    font_col = col.white_opened_cap_font
                else:
                    fill_col = col.white_fill
                    outline_col = col.white_outline
                    font_col = col.white_font

            cap_draw.rounded_rectangle(
                xy = (
                    50*(x+1) + 708*x,
                    50*(y+1) + 292*y,
                    (50+708) * (x+1),
                    (50+292) * (y+1)
                ),
                radius = 10,
                fill = fill_col,
                outline = outline_col,
                width = 2
            )
            cap_draw.text(
                xy = (
                    50*(x+1) + 708*x + 708/2,
                    50*(y+1) + 292*y + 292/2
                ),
                text = str(word).upper(),
                fill = font_col,
                font = font,
                anchor = 'mm'
            )
    
    # Filling the players' field
    for x in range(5):
        for y in range(5):
            word = order[x*5 + y]
            if word in opened_words:
                if word in team1_words:
                    fill_col = col.red_fill
                    outline_col = col.red_fill
                    font_col = col.red_font
                elif word in team2_words:
                    fill_col = col.blue_fill
                    outline_col = col.blue_fill
                    font_col = col.blue_font
                elif word == endgame_word:
                    fill_col = col.black_fill
                    outline_col = col.black_fill
                    font_col = col.black_font
                elif word in other_words:
                    fill_col = col.white_opened_pl_fill
                    outline_col = col.white_opened_pl_outline
                    font_col = col.white_opened_pl_font
            else:
                fill_col = col.white_fill
                outline_col = col.white_outline
                font_col = col.white_font

            pl_draw.rounded_rectangle(
                xy = (
                    50*(x+1) + 708*x,
                    50*(y+1) + 292*y,
                    (50+708) * (x+1),
                    (50+292) * (y+1)
                ),
                radius = 10,
                fill = fill_col,
                outline = outline_col,
                width = 2
            )
            pl_draw.text(
                xy = (
                    50*(x+1) + 708*x + 708/2,
                    50*(y+1) + 292*y + 292/2
                ),
                text = str(word).upper(),
                fill = font_col,
                font = font,
                anchor = 'mm'
            )

    os.makedirs(os.path.join(os.getcwd(), "images"), exist_ok=True)
    cap_img.save(os.path.join('images', 'cap_field.png'))
    pl_img.save(os.path.join('images', 'pl_field.png'))

def words(lang, dict_name):
    dictionary = open(os.path.join(os.getcwd(), 'dictionaries', lang, f'{dict_name}.txt'), 'r', encoding='utf-8')
    all_words = dictionary.read().lower().replace("ё", "е").split('\n')
    words = multiple_choice(all_words, 25)

    words1 = words.copy()
    endgame_word = random.choice(words1)
    words1.remove(endgame_word)
    first_team = random.random()
    if first_team <= 0.5:
        team1_words, words1 = multiple_choice(words1, 9, True)
        team2_words, other_words = multiple_choice(words1, 8, True)
    else:
        team2_words, words1 = multiple_choice(words1, 9, True)
        team1_words, other_words = multiple_choice(words1, 8, True)
    
    return tuple(team1_words), tuple(team2_words), endgame_word, tuple(other_words)
