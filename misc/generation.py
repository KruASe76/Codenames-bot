import math
import os
import random
from typing import Iterable, Sequence

from PIL import Image, ImageDraw

from misc.constants import font, big_font, Paths, FieldSizing, Colors


# noinspection PyUnboundLocalVariable
def field(
    team1_words: Iterable[str], team2_words: Iterable[str], endgame_word: str, no_team_words: Iterable[str],
    opened_words: Iterable[str], order: Sequence[str],
    uuid: str
) -> None:
    """
    Creates and saves captain and player fields as images from the given game word lists.

    :param team1_words: Red cards
    :param team2_words: Blue cards
    :param endgame_word: Black card
    :param no_team_words: White cards
    :param opened_words: "Used" words
    :param order: Order that the words should be displayed in
    :param uuid: Game uuid to save images without conflicts
    :return: None
    """

    img = Image.new("RGB", (FieldSizing.width, FieldSizing.height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Drawing two bottom rectangles with left words counter
    draw.rectangle(
        xy=(
            0,
            FieldSizing.height - FieldSizing.footer_height,
            FieldSizing.width / 2 - 1,
            FieldSizing.height - 1
        ),
        fill=Colors.red_fill,
    )
    red_words_left = 0
    for word in team1_words:
        if word not in opened_words:
            red_words_left += 1
    draw.text(
        xy=(
            FieldSizing.width / 4,
            FieldSizing.height - FieldSizing.footer_height / 2
        ),
        text=str(red_words_left),
        fill=Colors.red_font,
        font=big_font,
        anchor=FieldSizing.text_anchor
    )

    draw.rectangle(
        xy=(
            FieldSizing.width / 2,
            FieldSizing.height - FieldSizing.footer_height,
            FieldSizing.width - 1,
            FieldSizing.height - 1
        ),
        fill=Colors.blue_fill,
    )
    blue_words_left = 0
    for word in team2_words:
        if word not in opened_words:
            blue_words_left += 1
    draw.text(
        xy=(
            FieldSizing.width / 2 + FieldSizing.width / 4,
            FieldSizing.height - FieldSizing.footer_height / 2
        ),
        text=str(blue_words_left),
        fill=Colors.blue_font,
        font=big_font,
        anchor=FieldSizing.text_anchor
    )

    # Creating two separate images for two fields
    cap_img = img.copy()
    cap_draw = ImageDraw.Draw(cap_img)
    pl_img = img.copy()
    pl_draw = ImageDraw.Draw(pl_img)

    # Filling the captain's field
    for x in range(FieldSizing.card_count):
        for y in range(FieldSizing.card_count):
            word = order[x * FieldSizing.card_count + y]
            if word in team1_words:
                if word in opened_words:
                    fill_col = Colors.red_opened_fill
                    outline_col = Colors.red_opened_fill
                    font_col = Colors.red_opened_font
                else:
                    fill_col = Colors.red_fill
                    outline_col = Colors.red_fill
                    font_col = Colors.red_font
            elif word in team2_words:
                if word in opened_words:
                    fill_col = Colors.blue_opened_fill
                    outline_col = Colors.blue_opened_fill
                    font_col = Colors.blue_opened_font
                else:
                    fill_col = Colors.blue_fill
                    outline_col = Colors.blue_fill
                    font_col = Colors.blue_font
            elif word == endgame_word:
                if word in opened_words:
                    fill_col = Colors.black_opened_fill
                    outline_col = Colors.black_opened_fill
                    font_col = Colors.black_opened_font
                else:
                    fill_col = Colors.black_fill
                    outline_col = Colors.black_fill
                    font_col = Colors.black_font
            elif word in no_team_words:
                if word in opened_words:
                    fill_col = Colors.white_opened_cap_fill
                    outline_col = Colors.white_opened_cap_outline
                    font_col = Colors.white_opened_cap_font
                else:
                    fill_col = Colors.white_fill
                    outline_col = Colors.white_outline
                    font_col = Colors.white_font

            cap_draw.rounded_rectangle(
                xy=(
                    FieldSizing.card_spacing * (x + 1) + FieldSizing.card_width * x,
                    FieldSizing.card_spacing * (y + 1) + FieldSizing.card_height * y,
                    (FieldSizing.card_spacing + FieldSizing.card_width) * (x + 1),
                    (FieldSizing.card_spacing + FieldSizing.card_height) * (y + 1)
                ),
                radius=FieldSizing.card_radius,
                fill=fill_col,
                outline=outline_col,
                width=FieldSizing.card_outline_width
            )

            cap_draw.text(
                xy=(
                    FieldSizing.card_spacing * (x + 1) + FieldSizing.card_width * x + FieldSizing.card_width / 2,
                    FieldSizing.card_spacing * (y + 1) + FieldSizing.card_height * y + FieldSizing.card_height / 2
                ),
                text=str(word).upper(),
                fill=font_col,
                font=font,
                anchor=FieldSizing.text_anchor
            )

    # Filling the players' field
    for x in range(FieldSizing.card_count):
        for y in range(FieldSizing.card_count):
            word = order[x * FieldSizing.card_count + y]
            if word in opened_words:
                if word in team1_words:
                    fill_col = Colors.red_fill
                    outline_col = Colors.red_fill
                    font_col = Colors.red_font
                elif word in team2_words:
                    fill_col = Colors.blue_fill
                    outline_col = Colors.blue_fill
                    font_col = Colors.blue_font
                elif word == endgame_word:
                    fill_col = Colors.black_fill
                    outline_col = Colors.black_fill
                    font_col = Colors.black_font
                elif word in no_team_words:
                    fill_col = Colors.white_opened_pl_fill
                    outline_col = Colors.white_opened_pl_outline
                    font_col = Colors.white_opened_pl_font
            else:
                fill_col = Colors.white_fill
                outline_col = Colors.white_outline
                font_col = Colors.white_font

            pl_draw.rounded_rectangle(
                xy=(
                    FieldSizing.card_spacing * (x + 1) + FieldSizing.card_width * x,
                    FieldSizing.card_spacing * (y + 1) + FieldSizing.card_height * y,
                    (FieldSizing.card_spacing + FieldSizing.card_width) * (x + 1),
                    (FieldSizing.card_spacing + FieldSizing.card_height) * (y + 1)
                ),
                radius=FieldSizing.card_radius,
                fill=fill_col,
                outline=outline_col,
                width=FieldSizing.card_outline_width
            )

            pl_draw.text(
                xy=(
                    FieldSizing.card_spacing * (x + 1) + FieldSizing.card_width * x + FieldSizing.card_width / 2,
                    FieldSizing.card_spacing * (y + 1) + FieldSizing.card_height * y + FieldSizing.card_height / 2
                ),
                text=str(word).upper(),
                fill=font_col,
                font=font,
                anchor=FieldSizing.text_anchor
            )

    os.makedirs(Paths.img_dir, exist_ok=True)
    cap_img.save(Paths.cap_img(uuid))
    pl_img.save(Paths.pl_img(uuid))


def words(lang: str, dict_name: str) -> tuple[tuple[str], tuple[str], str, tuple[str]]:
    """
    Returns game words randomly picked from the given dictionary

    :param lang: Dictionary language
    :param dict_name: Dictionary name
    :return: Game words: red (tuple), blue (tuple), endgame (str), no team (tuple)
    """

    with open(Paths.dictionary(lang, dict_name), "r", encoding="utf-8") as dictionary:
        all_words = dictionary.read().lower().replace("ё", "е").split("\n")
    words: set[str] = set(random.sample(all_words, 25))

    endgame_word = random.sample(tuple(words), 1)[0]
    words.remove(endgame_word)

    first_team = math.floor(random.random() * 2)
    if first_team:
        team1_words = random.sample(tuple(words), 9)
        words.difference_update(team1_words)
        team2_words = random.sample(tuple(words), 8)
        no_team_words = words.difference(team2_words)
    else:
        team2_words = random.sample(tuple(words), 9)
        words.difference_update(team2_words)
        team1_words = random.sample(tuple(words), 8)
        no_team_words = words.difference(team1_words)

    return tuple(team1_words), tuple(team2_words), endgame_word, tuple(no_team_words)
