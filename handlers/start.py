import logging  # Импортируем библиотеку для ведения логов
from aiogram import types, Dispatcher, BaseMiddleware, Router  # Импортируем необходимые классы и модули из aiogram
from aiogram.dispatcher import router  # Импортируем роутер для обработки сообщений
from aiogram.filters import Command  # Импортируем фильтр для команд
from aiogram_dialog import DialogManager, StartMode  # Импортируем менеджер диалогов
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # Импортируем классы для создания клавиатур
from buy.buy import buy  # Импортируем функцию покупки
from handlers.table import register_handlers as register_tables_handlers  # Импортируем обработчики для таблиц
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton  # Импортируем классы для инлайн-клавиатур
from database.database import get_db_connection, get_user_counts  # Импортируем функции для работы с базой данных
from keyboards.tables_menu import leagues_router as leagues_router, LeagueSG  # Импортируем лиги

router = Router()  # Создаем роутер для обработки команд

# Обработчик команды /start
async def start_command(message: types.Message):
    user_id = message.from_user.id  # Получаем ID пользователя
    username = message.from_user.username  # Получаем имя пользователя
    first_name = message.from_user.first_name  # Получаем имя
    last_name = message.from_user.last_name  # Получаем фамилию

    try:
        conn = await get_db_connection()  # Получаем соединение с базой данных
        if conn is None:  # Проверяем, удалось ли подключиться
            await message.answer("Ошибка при подключении к базе данных. Попробуйте позже.")
            return

        async with conn.cursor() as cursor:  # Используем курсор для выполнения SQL-запросов
            await cursor.execute("SELECT subscription_active FROM users WHERE user_id = %s", (user_id,))
            user = await cursor.fetchone()  # Извлекаем данные пользователя

            if not user:  # Если пользователь не найден в базе данных
                # Добавляем нового пользователя с неактивной подпиской
                await cursor.execute(
                    "INSERT INTO users (user_id, username, first_name, last_name, subscription_active) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (user_id, username, first_name, last_name, 0)
                )
                await conn.commit()  # Подтверждаем изменения
                subscription_active = 0  # Устанавливаем статус подписки как неактивный
            else:
                subscription_active = user[0]  # Получаем статус подписки

        conn.close()  # Закрываем соединение с базой данных

        # Формируем клавиатуру для пользователя
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Таблицы")],
                [KeyboardButton(text="Купить")],
                [KeyboardButton(text="Матчи на сегодня")],
                [KeyboardButton(text="Помощь")]
            ],
            resize_keyboard=True  # Автоматически подстраиваем размер клавиатуры
        )

        # Сообщение для пользователей в зависимости от статуса подписки
        if subscription_active:
            await message.answer("Добро пожаловать! Выберите действие или /help", reply_markup=keyboard)
        else:
            await message.answer(
                "У вас нет активной подписки. Нажмите 'Купить', чтобы активировать.",
                reply_markup=keyboard
            )
    except Exception as e:  # Обработка исключений
        logging.error(f"Ошибка при обработке команды /start: {e}")  # Логируем ошибку
        await message.answer("Произошла ошибка. Попробуйте позже.")


# Обработчик для кнопки "Купить"
async def buy_command(message: types.Message):
    await message.answer("Вы выбрали покупку. Начинаем процесс покупки...")  # Уведомляем пользователя о начале покупки
    await buy(message)  # Вызываем функцию покупки


# Обработчик команды /help
@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Это бот по отображению таблиц и ближайших матчей команд из топ-5 самых сильных лиг мира 🇬🇧🇪🇸🇩🇪🇮🇹🇫🇷.\n"
                         "команды для работы с ботом: /start - активация/перезагрузка\n"
                         "/help Получить помощь, /buy Купить подписку\n"
                         "/tables Открыть меню с выбором таблицы.")


# Обработчик команды /tables
@router.message(Command("tables"))
async def tables_command(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(LeagueSG.select_league, mode=StartMode.RESET_STACK)  # Запускаем диалог выбора лиги


# Обработчик команды /stats для получения статистики пользователей
async def stats_command(message: types.Message):
    try:
        total_users, subscribed_users = await get_user_counts()  # Получаем общее количество пользователей и подписчиков
        await message.answer(
            f"Всего пользователей: {total_users}\n"
            f"Пользователей с подпиской: {subscribed_users}"
        )
    except Exception as e:  # Обработка исключений
        await message.answer(f"Ошибка при получении данных: {str(e)}")  # Сообщаем об ошибке


# Middleware для проверки подписки пользователя
class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):  # Проверяем, что событие - это сообщение
            if event.text in ["/start", "/buy"]:  # Если команда /start или /buy, пропускаем проверку
                return await handler(event, data)

            user_id = event.from_user.id  # Получаем ID пользователя
            if not await is_subscription_active(user_id):  # Проверяем, активна ли подписка
                await event.answer("Ваша подписка не активна. Используйте /buy для покупки подписки.")
                return  # Если подписка не активна, отправляем сообщение и прекращаем выполнение
        return await handler(event, data)  # В противном случае продолжаем обработку


# Функция для проверки активности подписки
async def is_subscription_active(user_id: int) -> bool:
    conn = await get_db_connection()  # Получаем соединение с базой данных
    if conn is None:  # Проверяем, удалось ли подключиться
        return False

    async with conn.cursor() as cursor:  # Используем курсор для выполнения SQL-запросов
        await cursor.execute("SELECT subscription_active FROM users WHERE user_id = %s", (user_id,))
        result = await cursor.fetchone()  # Извлекаем данные о подписке
        return result and result[0] == 1  # Возвращаем True, если подписка активна


# Регистрация обработчиков
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))  # Регистрируем обработчик команды /start
    dp.message.register(stats_command, Command("stats"))  # Регистрируем обработчик команды /stats
    dp.message.register(help_command, Command("help"))  # Регистрируем обработчик команды /help
    dp.message.register(tables_command, Command("tables"))  # Регистрируем обработчик команды /tables

    # Регистрация обработчиков для кнопок
    dp.message.register(help_command, lambda message: message.text == "Помощь")
    dp.message.register(buy_command, lambda message: message.text == "Купить")
    dp.message.register(help_command, lambda message: message.text == "Помощь")
    dp.message.register(tables_command, lambda message: message.text == "Таблицы")

    register_tables_handlers(dp)  # Регистрируем обработчики для таблиц
