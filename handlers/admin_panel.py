# handlers/admin_panel.py

import logging  # Импортируем библиотеку для ведения логов
from aiogram import Router  # Импортируем Router для обработки команд
from aiogram.filters import Command  # Импортируем фильтр для команд
from database.database import get_db_connection, get_user_counts  # Импортируем функции для работы с базой данных

# Создаем роутер для административных команд
router = Router()

# Укажите ID администратора
ADMIN_USER_ID = 688876136  # ID пользователя, который имеет права администратора

# Команда для получения данных пользователя по ID (доступна только администратору)
@router.message(Command('user_data'))
async def user_data(message):
    # Проверяем, является ли отправитель администратором
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("У вас нет прав для использования этой команды.")  # Ответ для неадминистратора
        return

    # Извлекаем ID пользователя из текста сообщения
    user_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    if not user_id:  # Проверяем, указан ли ID пользователя
        await message.answer("Пожалуйста, укажите ID пользователя.")
        return

    # Получаем соединение с базой данных
    conn = await get_db_connection()
    if conn is None:  # Проверяем, удалось ли подключиться к базе данных
        await message.answer("Ошибка при подключении к базе данных. Попробуйте позже.")
        return

    try:
        # Используем курсор для выполнения SQL-запроса
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT user_id, username, first_name, last_name, subscription_active, subscription_date, subscription_paid, blocked, is_blocked FROM users WHERE user_id = %s",
                (user_id,)
            )
            user_data = await cursor.fetchone()  # Извлекаем данные пользователя

        if user_data:  # Если данные пользователя найдены
            await message.answer(
                f"Данные пользователя {user_data[1]} ({user_data[2]} {user_data[3]}):\n"
                f"Активная подписка: {'Да' if user_data[4] else 'Нет'}\n"
                f"Дата подписки: {user_data[5] if user_data[5] else 'Не указана'}\n"
                f"Оплачена подписка: {'Да' if user_data[6] else 'Нет'}\n"
                f"Заблокирован: {'Да' if user_data[7] else 'Нет'}\n"
                f"Статус блокировки: {'Заблокирован' if user_data[8] else 'Не заблокирован'}"
            )
        else:  # Если пользователь не найден
            await message.answer(f"Пользователь с ID {user_id} не найден.")
    except Exception as e:  # Обработка исключений
        logging.error(f"Ошибка при получении данных пользователя: {e}")  # Логируем ошибку
        await message.answer("Ошибка при получении данных пользователя. Попробуйте позже.")
    finally:
        conn.close()  # Закрываем соединение с базой данных

# Команда для получения статистики подписок (доступна только администратору)
@router.message(Command('subscriptions_count'))
async def subscriptions_count(message):
    # Проверяем, является ли отправитель администратором
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("У вас нет прав для использования этой команды.")
        return

    # Получаем общее количество пользователей и количество подписчиков
    total_users, subscribed_users = await get_user_counts()

    # Отправляем статистику администратору
    await message.answer(
        f"Общее количество пользователей: {total_users}\n"
        f"Количество пользователей с активной подпиской: {subscribed_users}"
    )

# Команда для активации/деактивации подписки пользователя (доступна только администратору)
@router.message(Command('toggle_subscription'))
async def toggle_subscription(message):
    # Проверяем, является ли отправитель администратором
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("У вас нет прав для использования этой команды.")
        return

    # Разбиваем текст сообщения на части
    parts = message.text.split()
    if len(parts) < 3:  # Проверяем, указаны ли ID пользователя и действие
        await message.answer("Пожалуйста, укажите ID пользователя и новое состояние подписки (активировать/деактивировать).")
        return

    user_id = parts[1]  # Извлекаем ID пользователя
    action = parts[2].lower()  # Извлекаем действие и приводим к нижнему регистру

    # Проверяем, является ли действие корректным
    if action not in ['активировать', 'деактивировать']:
        await message.answer("Неверное действие. Используйте 'активировать' или 'деактивировать'.")
        return

    # Устанавливаем новое состояние подписки
    new_status = 1 if action == 'активировать' else 0

    # Получаем соединение с базой данных
    conn = await get_db_connection()
    if conn is None:
        await message.answer("Ошибка при подключении к базе данных. Попробуйте позже.")
        return

    try:
        # Используем курсор для выполнения SQL-запроса на обновление статуса подписки
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET subscription_active = %s WHERE user_id = %s", (new_status, user_id)
            )
            await conn.commit()  # Подтверждаем изменения в базе данных

        # Отправляем сообщение об успешном изменении статуса подписки
        await message.answer(f"Подписка пользователя {user_id} успешно {'активирована' if new_status else 'деактивирована'}.")
    except Exception as e:  # Обработка исключений
        logging.error(f"Ошибка при обновлении статуса подписки: {e}")  # Логируем ошибку
        await message.answer("Ошибка при обновлении статуса подписки. Попробуйте позже.")
    finally:
        conn.close()  # Закрываем соединение с базой данных
