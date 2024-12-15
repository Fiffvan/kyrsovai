import aiomysql  # Импортируем библиотеку для работы с MySQL асинхронно
import os  # Импортируем модуль для работы с операционной системой
from dotenv import load_dotenv  # Импортируем функцию для загрузки переменных окружения из .env файла

# Загружаем переменные окружения из .env файла
load_dotenv()


async def get_db_connection():
    """Создает подключение к базе данных."""
    try:
        # Выводим информацию о подключении для отладки
        print(f"Подключаемся к базе данных: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")

        # Устанавливаем асинхронное соединение с базой данных MySQL
        conn = await aiomysql.connect(
            host=os.getenv("DB_HOST"),  # Хост базы данных
            port=int(os.getenv("DB_PORT")),  # Порт базы данных
            user=os.getenv("DB_USER"),  # Имя пользователя для подключения
            password=os.getenv("DB_PASSWORD"),  # Пароль пользователя
            db=os.getenv("DB_NAME"),  # Имя базы данных
        )

        print("Соединение с базой данных установлено.")  # Подтверждение успешного подключения
        return conn  # Возвращаем объект соединения
    except Exception as e:
        # Логируем ошибку при подключении к базе данных
        print(f"Ошибка при подключении к базе данных: {e}")
        return None  # Возвращаем None в случае ошибки подключения


async def get_user_counts():
    """Получает количество пользователей и подписчиков."""

    # SQL-запрос для получения общего количества пользователей
    query_total_users = "SELECT COUNT(*) FROM users;"

    # SQL-запрос для получения количества пользователей с активной подпиской
    query_subscribed_users = "SELECT COUNT(*) FROM users WHERE subscription_active = 1;"

    # Устанавливаем соединение с базой данных
    async with await get_db_connection() as conn:
        # Создаем курсор для выполнения SQL-запросов
        async with conn.cursor() as cursor:
            # Выполняем запрос для получения общего количества пользователей
            await cursor.execute(query_total_users)
            total_users = await cursor.fetchone()  # Извлекаем результат запроса

            # Выполняем запрос для получения количества пользователей с активной подпиской
            await cursor.execute(query_subscribed_users)
            subscribed_users = await cursor.fetchone()  # Извлекаем результат запроса

    # Возвращаем общее количество пользователей и количество подписчиков
    return total_users[0], subscribed_users[0]
