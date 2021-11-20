with open('dict.txt', 'r', encoding='utf-8') as file:
    dictt = file.read()

dictt = dictt.replace(chr(173), '')

dicttt = dictt.split(', ')

with open('dictionaries\\ru\\all.txt', 'w', encoding='utf-8') as file:
    wr = '\n'.join(dicttt)
    file.write(wr)