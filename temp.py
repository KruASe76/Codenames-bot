import generation as gen

uhd = gen.UltraHD()
col = gen.Colors(False)

team1_words, team2_words, endgame_word, other_words, opened_words = gen.words('ru', 'deep')

gen.field(uhd, col, team1_words, team2_words, endgame_word, other_words, opened_words)

available_words = list(set(team1_words + team2_words + [endgame_word] + other_words) - set(opened_words))
print(available_words)