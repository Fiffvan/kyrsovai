from aiogram import Bot
from aiogram.types import BotCommand

async def set_bot_commands(bot: Bot):
    """Устанавливает команды в меню бота."""
    commands = [
        BotCommand(command="/start", description="Начать работу с ботом"),
        BotCommand(command="/help", description="Получить помощь"),
        BotCommand(command="/buy", description="Купить подписку"),
        BotCommand(command="/tables", description="Открыть меню с выбором таблицы чемпионата"),
    ]
    await bot.set_my_commands(commands)
