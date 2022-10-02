from dataclasses import dataclass


@dataclass
class CogName:
    singular: str
    plural: str

@dataclass
class Commands:
    ...

@dataclass
class Errors:
    no_permission: str
    guild_only: str


@dataclass
class Localization:
    cogs: dict[str: CogName]
    commands: Commands
    errors: Errors


messages = {
    "en": Localization(
        cogs={
            "Game": CogName(
                singular="Game command",
                plural="Game commands"
            ),
            "Settings": CogName(
                singular="Setting command",
                plural="Setting commands"
            )
        },
        commands=Commands(
            
        ),
        errors=Errors(
            no_permission="Not enough permissions to call this command!",
            guild_only="This command is guild-only!"
        )
    ),
    "ru": Localization(
        cogs={
            "Game": CogName(
                singular="Команда для игры",
                plural="Команды для игры"
            ),
            "Settings": CogName(
                singular="Команда настроек",
                plural="Команды настроек"
            )
        },
        commands=Commands(
            
        ),
        errors=Errors(
            no_permission="Недостаточно прав для вызова этой команды!",
            guild_only="Эта команда работает только на сервере!"
        )
    )
}
