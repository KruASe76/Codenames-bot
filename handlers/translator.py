from discord import Locale
from discord.app_commands import Translator, locale_str, TranslationContextTypes, TranslationContextLocation

from misc.messages import messages


class CodenamesTranslator(Translator):  # only used for command and parameter descriptions
    async def translate(self, string: locale_str, locale: Locale, context: TranslationContextTypes) -> str | None:
        if context.location not in (
            TranslationContextLocation.command_description, TranslationContextLocation.parameter_description
        ):
            return

        if locale == Locale.russian:
            return messages["ru"].help[string.message].brief.replace("**", "")

        return messages["en"].help[string.message].brief.replace("**", "")
