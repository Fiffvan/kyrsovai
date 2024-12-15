import asyncio  # Импортируем модуль для работы с асинхронным программированием
import logging  # Импортируем модуль для ведения логов
from aiogram import Bot, Dispatcher  # Импортируем классы Bot и Dispatcher из библиотеки aiogram
from aiogram.fsm.storage.memory import MemoryStorage  # Импортируем хранилище в памяти для состояния
from config_data.config import load_config  # Импортируем функцию для загрузки конфигурации
from handlers.menu import set_bot_commands  # Импортируем функцию для установки команд бота
from handlers.start import register_handlers as register_start_handlers  # Импортируем обработчики старта
from handlers.table import register_handlers as register_table_handlers  # Импортируем обработчики таблиц
from buy.buy import router as buy_router  # Импортируем роутер из buy.py
from handlers.table import register_today_matches_handler  # Импортируем обработчик для сегодняшних матчей
from aiogram_dialog import DialogManager  # Импортируем менеджер диалогов
from handlers.start import SubscriptionMiddleware  # Импортируем middleware для проверки подписки
from keyboards.tables_menu import leagues_dialog  # Импортируем диалог для выбора лиги
from aiogram.dispatcher.router import Router  # Импортируем класс Router
from keyboards.tables_menu import leagues_router as leagues_router  # Импортируем роутер для лиг
from handlers.subscription_middleware import SubscriptionMiddleware  # Импортируем middleware для подписки
from handlers.admin_panel import router as admin_panel_router  # Импортируем роутер для административной панели

from aiogram_dialog import setup_dialogs  # Импортируем функцию для настройки диалогов
from utils.api import APIFootball  # Импортируем класс для работы с API футбольной статистики
from dotenv import load_dotenv  # Импортируем функцию для загрузки переменных окружения
import os  # Импортируем модуль для работы с операционной системой
from aiogram.client.session.aiohttp import AiohttpSession
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token="bot token", session=session)
# Настройка логирования
logger = logging.getLogger(__name__)

async def main():
    # Конфигурация логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )

    logger.info("Starting bot")  # Логируем начало работы бота

    config = load_config()  # Загружаем конфигурацию

    # Инициализация бота и диспетчера
    bot = Bot(token=config.tg_bot.token)  # Создаем экземпляр бота с токеном из конфигурации
    dp = Dispatcher(storage=MemoryStorage())  # Создаем диспетчер с хранилищем в памяти

    # Загружаем переменные окружения
    load_dotenv()

    # Получаем ключ API из переменных окружения
    api_key = os.getenv("API_KEY")  # Извлекаем ключ API
    football_api = APIFootball(api_key=api_key, season=int(os.getenv("SEASON")))  # Инициализируем API футбольной статистики

    # Применяем middleware для подписки
    dp.message.middleware(SubscriptionMiddleware())  # Подключаем middleware для проверки подписки

    logger.info("Registering handlers...")  # Логируем процесс регистрации обработчиков

    # Регистрация обработчиков
    register_start_handlers(dp)  # Регистрируем обработчики для команды /start
    register_table_handlers(dp)  # Регистрируем обработчики для таблиц
    dp.message.middleware(SubscriptionMiddleware())  # Подключаем middleware для подписки
    dp.include_router(admin_panel_router)  # Включаем роутер для административной панели

    # Включаем роутеры
    dp.include_router(buy_router)  # Включаем роутер для обработки покупок
    register_today_matches_handler(dp)  # Регистрируем обработчик для сегодняшних матчей

    # Регистрируем диалоги
    dp.include_router(leagues_router)  # Включаем роутер для лиг

    # Настраиваем диалоги
    setup_dialogs(dp)  # Настраиваем диалоги для использования в боте

    await set_bot_commands(bot)  # Устанавливаем команды бота

    logger.info("Starting polling...")  # Логируем начало опроса

    await bot.delete_webhook(drop_pending_updates=True)  # Удаляем вебхук (если был установлен) и сбрасываем ожидающие обновления
    await dp.start_polling(bot)  # Запускаем опрос обновлений от Telegram

if __name__ == "__main__":
    asyncio.run(main())  # Запускаем основную асинхронную функцию
