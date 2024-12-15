from aiogram import BaseMiddleware, types  # Импортируем базовый класс Middleware и типы из библиотеки aiogram
from database.database import get_db_connection  # Импортируем функцию для получения соединения с базой данных
import logging  # Импортируем модуль для ведения логов


class SubscriptionMiddleware(BaseMiddleware):
    """Middleware для проверки статуса подписки пользователя перед обработкой сообщений."""

    async def __call__(self, handler, event, data):
        """Метод, который вызывается при каждом событии."""
        # Проверяем, является ли событие сообщением и содержит ли текст
        if isinstance(event, types.Message) and event.text:
            user_id = event.from_user.id  # Получаем ID пользователя из события

            # Пропускаем команды /start и /buy, чтобы не проверять подписку
            if event.text.startswith("/start") or event.text.startswith("/buy"):
                return await handler(event, data)  # Передаем управление следующему обработчику

            # Подключение к базе данных для проверки статуса подписки
            conn = await get_db_connection()  # Получаем соединение с базой данных

            if conn is None:  # Если соединение не удалось получить
                return await handler(event, data)  # Передаем управление следующему обработчику

            try:
                # Получаем статус подписки пользователя из базы данных
                async with conn.cursor() as cursor:  # Открываем курсор для выполнения запроса
                    await cursor.execute("SELECT subscription_active FROM users WHERE user_id = %s",
                                         (user_id,))  # Выполняем запрос
                    result = await cursor.fetchone()  # Получаем результат запроса

                if result:  # Если результат не пустой
                    subscription_active = result[0]  # Извлекаем статус подписки

                    # Если подписка не активна
                    if not subscription_active:
                        await event.answer(
                            "Ваша подписка не активна. Используйте /buy для покупки подписки.")  # Отправляем сообщение пользователю
                        return  # Завершаем выполнение, не передавая управление дальше
                else:
                    await event.answer("Пользователь не найден в базе данных.")  # Если пользователь не найден
                    return  # Завершаем выполнение

            except Exception as e:  # Обрабатываем возможные исключения
                # Логируем ошибку подключения к базе данных или выполнения запроса
                logging.error(f"Ошибка при проверке подписки: {e}")
            finally:
                conn.close()  # Закрываем соединение с базой данных

        return await handler(event, data)  # Передаем управление следующему обработчику
