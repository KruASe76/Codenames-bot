from dataclasses import dataclass


@dataclass
class HelpCommand:
    command_list: str
    guild: str
    moderator: str
    moderator_shortened: str
    about_moderator: str
    note: str
    hint: str
    command: str

@dataclass
class PlayersCommand:
    player_list: str
    final_player_list: str
    team1: str
    team2: str
    no_team: str
    empty_list: str

@dataclass
class StartCommand:
    lang_selection_title: str
    lang_selection_desc: str
    dict_selection_title: str
    dict_selection_desc: str
    dict_selected: str
    cap_selection_title: str
    cap_selection_desc: str
    cap_selected_title: str
    cap_selected_desc: str

@dataclass
class StatsCommand:
    smbs_stats: str
    playing_since: str
    total: str
    captain: str
    team: str
    games_played: str
    games_won: str
    winrate: str
    note: str

@dataclass
class PrefixCommand:
    prefix_changed_title: str
    prefix_changed_desc: str
    new_prefix: str
    prefix_deleted: str

@dataclass
class LanguageCommand:
    title: str
    desc_current: str
    desc_new: str
    desc_aborted: str

@dataclass
class Commands:
    help: HelpCommand
    players: PlayersCommand
    start: StartCommand
    stats: StatsCommand
    prefix: PrefixCommand
    language: LanguageCommand


@dataclass
class Game:
    red: str
    blue: str

    start_announcement: str
    start_notification_title: str
    start_notification_desc_cap: str
    start_notification_desc_pl: str

    waiting_title: str
    waiting_desc_cap: str
    waiting_desc_pl: str
    pl_move_instructions: str

    cap_move_request_title: str
    cap_move_request_desc: str
    cap_move_accepted: str
    cap_move_notification_title: str
    cap_move_notification_desc: str

    success_title: str
    success_desc_guild: str
    success_desc_dm: str
    opponents_success_title: str
    opponents_success_desc: str

    miss_title: str
    miss_desc_other_team_guild: str
    miss_desc_other_team_dm: str
    miss_desc_no_team_guild: str
    miss_desc_no_team_dm: str
    miss_desc_endgame_guild: str
    miss_desc_endgame_dm: str
    opponents_miss_title: str
    opponents_miss_desc: str  # Only for no_team reason

    lucky_title: str
    lucky_desc_your_team: str
    lucky_desc_endgame: str

    game_over_title: str
    game_over_desc_all: str
    game_over_desc_endgame: str
    your_team_won_title: str
    your_team_won_desc: str
    your_team_lost_title: str
    your_team_lost_desc: str

    voting_for_stopping_title: str
    voting_for_stopping_desc: str
    game_stopped_title: str
    game_stopped_desc: str
    game_continued_title: str
    game_continued_desc: str


@dataclass
class HelpAndBrief:
    help: str
    brief: str = None
    
    def __post_init__(self):
        self.brief = self.brief or self.help


@dataclass
class CogName:
    singular: str
    plural: str


@dataclass
class Errors:
    title: str
    no_permission: str
    guild_only: str
    invalid_command: str
    already_in_team: str
    invalid_team: str
    not_registered: str
    not_enough_players: str
    too_many_players: str
    never_played: str


@dataclass
class Localization:
    game: Game
    help: dict[str, HelpAndBrief]
    cogs: dict[str, CogName]
    commands: Commands
    errors: Errors


messages = {
    "en": Localization(
        game=Game(
            red="RED",
            blue="BLUE",
            start_announcement="GAME STARTED!",
            start_notification_title="Game started",
            start_notification_desc_cap="**You are the captain of the {} team**\n\nYour teammates are:\n{}",
            start_notification_desc_pl="**You're a member of the {} team**\n\nThe captain of your team is {}\n\n"
                                       "Your teammates are:\n{}",
            waiting_title="Waiting for move",
            waiting_desc_cap="Captain of **{}** team",
            waiting_desc_pl="Players of **{}** team",
            pl_move_instructions="Type words you want to open in response messages.\n"
                                 "To **FINISH THE MOVE** type **`0`**\nTo **STOP THE GAME** type **`000`**",
            cap_move_request_title="Your turn",
            cap_move_request_desc="Type a word and a number in response message, for example: **`{}`**",
            cap_move_accepted="Move accepted",
            cap_move_notification_title="Captain of **{}** team has made a move",
            cap_move_notification_desc="The move contains:\n**`{}`**",
            success_title="Success!",
            success_desc_guild="You guessed!",
            success_desc_dm="Your team opened the word **`{}`** that **belongs to ше**!",
            opponents_success_title="Opponent's success",
            opponents_success_desc="The opponent team opened the word **`{}`** that **belongs to it**",
            miss_title="Miss",
            miss_desc_other_team_guild="Unfortunately, this word **belongs to the opponent team**",
            miss_desc_other_team_dm="Your team opened the word **`{}`** that **belongs to the opponent team**",
            miss_desc_no_team_guild="Unfortunately, this word **doesn't belong to any team**",
            miss_desc_no_team_dm="Your team opened the word **`{}`** that **doesn't belong to any team**",
            miss_desc_endgame_guild="Unfortunately, this word **is an endgame one**",
            miss_desc_endgame_dm="Your team opened the word **`{}`** that **is an endgame one**",
            opponents_miss_title="Opponent's miss",
            opponents_miss_desc="The opponent team opened the word **`{}`** that **doesn't belong to any team**",
            lucky_title="Lucky!",
            lucky_desc_your_team="The opponent team opened the word **`{}`** that **belongs to your team**",
            lucky_desc_endgame="The opponent team opened the word **`{move}`** that **is an endgame one**",
            game_over_title="Game over!",
            game_over_desc_all="**{} team won!**\nThey opened all their words",
            game_over_desc_endgame="**{} team won!**\n{} team opened an endgame word",
            your_team_won_title="Your team won!",
            your_team_won_desc="Keep it up!",
            your_team_lost_title="Your team lost!",
            your_team_lost_desc="Good luck in the next game!",
            voting_for_stopping_title="Stopping the game",
            voting_for_stopping_desc="**Do you really want to stop playing?**\n\nAll players have 15 seconds to vote",
            game_stopped_title="GAME STOPPED",
            game_stopped_desc="Most players voted for game stopping",
            game_continued_title="GAME CONTINUES",
            game_continued_desc="Most players voted against game stopping"
        ),
        help={
            "register": HelpAndBrief(
                help="Register for the game.\nIf you will not provide a team it will be picked randomly when the game "
                     "starts.\nTo change the team call the command again with new number; to reset team, do not input "
                     "any number.",
                brief="Register for the game"
            ),
            "leave": HelpAndBrief(
                help="Cancel registration for the game"
            ),
            "clear": HelpAndBrief(
                help="Clear the list of registered players"
            ),
            "players": HelpAndBrief(
                help="Show registered players"
            ),
            "start": HelpAndBrief(
                help="Start the game.\nIf there are players without a team they will be evenly distributed.",
                brief="Start the game"
            ),
            "stats": HelpAndBrief(
                help="Show player's statistics"
            ),
            "prefix": HelpAndBrief(
                help="Change the bot's prefix.\nTo set it to default (`cdn`) do not provide any.",
                brief="Change the bot's prefix, empty prefix -> default"
            ),
            "language": HelpAndBrief(
                help="Change the language of the bot's messages (**EN**/**RU**)"
            )
        },
        cogs={
            "game": CogName(
                singular="Game command",
                plural="Game commands"
            ),
            "settings": CogName(
                singular="Setting command",
                plural="Setting commands"
            )
        },
        commands=Commands(
            help=HelpCommand(
                command_list="Command list",
                guild="Server",
                moderator="Moderator",
                moderator_shortened="Mod",
                about_moderator="Moderator is the member who can manage messages in the channel where the command was "
                                "called",
                note="Note",
                hint="Learn a more detailed description of the command:",
                command="command"
            ),
            players=PlayersCommand(
                player_list="Player list",
                final_player_list="Final player list",
                team1="Team 1",
                team2="Team 2",
                no_team="No team",
                empty_list="Nobody is ready to play :("
            ),
            start=StartCommand(
                lang_selection_title="Select game language",
                lang_selection_desc="**en** - English\n**ru** - Russian\n\nType the choice in response message",
                dict_selection_title="Select dictionary",
                dict_selection_desc="You have 15 seconds to choose",
                dict_selected="Dictionary selected",
                cap_selection_title="**{}** team: Voting for the captain",
                cap_selection_desc="**R** - Random captain\n\n{}\n\nYou have 15 seconds to vote",
                cap_selected_title="**{}** team: Captain selected",
                cap_selected_desc="Your captain is {}"
            ),
            stats=StatsCommand(
                smbs_stats="{}'s statistics",
                playing_since="Playing Codenames since {}",
                total="Total",
                captain="As captain",
                team="In the team",
                games_played="Games played",
                games_won="Games won",
                winrate="Winrate",
                note="Codenames is a **team game**, so the winrate statistics **do not** exactly reflect player's skill"
            ),
            prefix=PrefixCommand(
                prefix_changed_title="Prefix changed",
                prefix_changed_desc="{}\nDefault one **`cdn`** and bot ping are still valid",
                new_prefix="New prefix:\n**`{}`**\n",
                prefix_deleted="Custom prefix deleted"
            ),
            language=LanguageCommand(
                title="Language settings",
                desc_current="**Current language: {} {}**\n\nSelect new language using reactions\n\n"
                             "_You have 15 seconds_",
                desc_new="**New language: {} {}**",
                desc_aborted="Aborted"
            )
        ),
        errors=Errors(
            title="Error",
            no_permission="Not enough permissions to call this command",
            guild_only="This command is server-only",
            invalid_command="Invalid command",
            already_in_team="You are already in that team",
            invalid_team="**Invalid team number**\nThere are only 2 teams in the game.\nSelect one of them or do not "
                         "type the number to pick randomly.",
            not_registered="You are not registered to the game",
            not_enough_players="**Not enough players**\nEach team must have **at least 2** players.",
            too_many_players="**Too much players**\nEach team must have **no more than 25** players.",
            never_played="{} haven't played Codenames yet"
        )
    ),
    "ru": Localization(
        game=Game(
            red="КРАСНЫХ",
            blue="СИНИХ",
            start_announcement="ИГРА НАЧАЛАСЬ!",
            start_notification_title="Игра началась",
            start_notification_desc_cap="**Вы - капитан команды {}**\n\nС Вами в команде:\n{}",
            start_notification_desc_pl="**Вы - участник команды {}**\n\nКапитан Вашей команды - {}\n\nС Вами в "
                                       "команде:\n{}",
            waiting_title="Ожидание хода",
            waiting_desc_cap="Капитан команды **{}**",
            waiting_desc_pl="Игроки команды **{}**",
            pl_move_instructions="В ответных сообщениях напишите слова, которые вы хотите открыть.\nЧтобы "
                                 "**ЗАКОНЧИТЬ ХОД**, напишите **`0`**\nЧтобы **ОСТАНОВИТЬ ИГРУ**, напишите **`000`**",
            cap_move_request_title="Ваш ход",
            cap_move_request_desc="В ответном сообщении напишите слово и число, например: **`{}`**",
            cap_move_accepted="Ход принят",
            cap_move_notification_title="Капитан команды **{}** сделал ход",
            cap_move_notification_desc="Ход содержит:\n**`{}`**",
            success_title="Успех!",
            success_desc_guild="Вы угадали!",
            success_desc_dm="Ваша команда открыла слово **`{}`**, которое **принадлежит ей**!",
            opponents_success_title="Успех противника",
            opponents_success_desc="Команда противника открыла слово **`{}`**, которое **принадлежит ей**",
            miss_title="Промах",
            miss_desc_other_team_guild="К сожалению, это слово **принадлежит команде противника**",
            miss_desc_other_team_dm="Ваша команда открыла слово **`{}`**, которое **принадлежит команде противника**",
            miss_desc_no_team_guild="К сожалению, это слово **не принадлежит ни одной команде**",
            miss_desc_no_team_dm="Ваша команда открыла слово **`{}`**, которое **не принадлежит ни одной команде**",
            miss_desc_endgame_guild="К сожалению, это слово **положит конец игре**",
            miss_desc_endgame_dm="Ваша команда открыла слово **`{}`**, которое **положит конец игре**",
            opponents_miss_title="Промах оппонента",
            opponents_miss_desc="Команда противника открыла слово **`{}`**, которое **е принадлежит ни одной команде**",
            lucky_title="Удача!",
            lucky_desc_your_team="Команда противника открыла слово **`{}`**, которое **принадлежит вашей команде**",
            lucky_desc_endgame="Команда противника открыла слово **`{}`**, которое **положит конец игре**",
            game_over_title="Игра окончена!",
            game_over_desc_all="**Команда {} победила!**\nОни открыли все свои слова",
            game_over_desc_endgame="**Команда {} победила!**\nКоманда {} открыла слово, положившее конец игре",
            your_team_won_title="Ваша команда победила!",
            your_team_won_desc="Так держать!",
            your_team_lost_title="Ваша команда потерпела поражение!",
            your_team_lost_desc="Удачи в следующей игре!",
            voting_for_stopping_title="Остановка игры",
            voting_for_stopping_desc="**Вы уверены, что хотите прекратить игру?**\n\n"
                                     "Всем игрокам на голосование дается 15 секунд",
            game_stopped_title="ИГРА ПРЕКРАЩЕНА",
            game_stopped_desc="Большинство игроков проголосовало за остановку игры",
            game_continued_title="ИГРА ПРОДОЛЖАЕТСЯ",
            game_continued_desc="Большинство игроков проголосовало против остановки игры"
        ),
        help={
            "register": HelpAndBrief(
                help="Зарегистрироваться на игру.\nЕсли не указать команду, она будет выбрана случайно перед началом "
                     "игры.\nЧтобы поменять команду, нужно вызвать команду еще раз, указав другой номер; чтобы "
                     "сбросить выбор команды, номер указывать не нужно.",
                brief="Зарегистрироваться на игру"
            ),
            "leave": HelpAndBrief(
                help="Отменить регистрацию на игру"
            ),
            "clear": HelpAndBrief(
                help="Очистить список зарегистрированных игроков"
            ),
            "players": HelpAndBrief(
                help="Показать зарегистрированных игроков"
            ),
            "start": HelpAndBrief(
                help="Начать игру.\nЕсли есть игроки без команды, они будут равномерно распределены.",
                brief="Начать игру"
            ),
            "stats": HelpAndBrief(
                help="Показать статистику игрока"
            ),
            "prefix": HelpAndBrief(
                help="Изменить префикс бота.\nЧтобы сбросить до префикса по умолчанию, новый указывать не нужно.",
                brief="Изменить префикс бота, пустой префикс -> по умолчанию"
            ),
            "language": HelpAndBrief(
                help="Изменить язык сообщений бота (**РУС**/**АНГ**)"
            )
        },
        cogs={
            "game": CogName(
                singular="Команда для игры",
                plural="Команды для игры"
            ),
            "settings": CogName(
                singular="Команда настроек",
                plural="Команды настроек"
            )
        },
        commands=Commands(
            help=HelpCommand(
                command_list="Список команд",
                guild="Сервер",
                moderator="Модератор",
                moderator_shortened="Модер",
                about_moderator="Модератор - это пользователь, который имеет право управления сообщениями в канале, "
                                "где была вызвана команда",
                note="Заметка",
                hint="Получить более подробное описание команды:",
                command="команда"
            ),
            players=PlayersCommand(
                player_list="Список игроков",
                final_player_list="Окончательный список игроков",
                team1="Команда 1",
                team2="Команда 2",
                no_team="Без команды",
                empty_list="Никто не готов играть :("
            ),
            start=StartCommand(
                lang_selection_title="Выберите язык игры",
                lang_selection_desc="**ru** - Русский\n**en** - Английский\n\nНапишите свой выбор в ответном сообщении",
                dict_selection_title="Выберите словарь",
                dict_selection_desc="На решение дается 15 секунд",
                dict_selected="Словарь выбран",
                cap_selection_title="Команда **{}**: Голосование за капитана",
                cap_selection_desc="**R** - Случайный капитан\n\n{}\n\nНа голосование дается 15 секунд",
                cap_selected_title="Команда **{}**: Капитан выбран",
                cap_selected_desc="Ваш капитан - {}"
            ),
            stats=StatsCommand(
                smbs_stats="Статистика {}",
                playing_since="Играет в Codenames с {}",
                total="Всего",
                captain="Как капитан",
                team="В команде",
                games_played="Игры",
                games_won="Победы",
                winrate="Винрейт",
                note="Codenames - **командная игра**, поэтому статистика побед игрока **не может** точно отражать его "
                     "мастерство"
            ),
            prefix=PrefixCommand(
                prefix_changed_title="Префикс изменен",
                prefix_changed_desc="{}\nУстановленный по умолчанию **`cdn`** и пинг бота все также работают",
                new_prefix="Новый префикс:\n**`{}`**\n",
                prefix_deleted="Префикс сервера сброшен"
            ),
            language=LanguageCommand(
                title="Настройки языка",
                desc_current="**Установленный язык: {} {}**\n\nВыберите новый язык посредством реакций\n\n"
                             "_Для выбора дается 15 секунд_",
                desc_new="**Новый язык: {} {}**",
                desc_aborted="Отменено"
            )
        ),
        errors=Errors(
            title="Ошибка",
            no_permission="Недостаточно прав для вызова этой команды",
            guild_only="Эта команда работает только на сервере",
            invalid_command="Такой команды не существует",
            already_in_team="Вы уже в этой команде",
            invalid_team="**Недопустимый номер команды**\nВ игре есть только две команды.\nМожно выбрать одну из них "
                         "или не выбирать, и тогда она будет случайной.",
            not_registered="Вы и без того не зарегистрированы",
            not_enough_players="**Недостаточно игроков**\nВ каждой команде должно быть **хотя бы 2** игрока.",
            too_many_players="**Слишком много игроков**\nВ каждой команде должно быть **не более 25** игроков.",
            never_played="{} еще не играл в Codenames"
        )
    )
}
