from dataclasses import dataclass  # Импортируем декоратор dataclass для упрощения создания классов
from environs import Env  # Импортируем библиотеку для работы с переменными окружения

@dataclass
class Database:
    """Класс для хранения конфигурации базы данных."""
    host: str  # Хост базы данных
    port: int  # Порт базы данных
    user: str  # Имя пользователя для подключения к базе данных
    password: str  # Пароль пользователя
    name: str  # Имя базы данных

@dataclass
class TgBot:
    """Класс для хранения конфигурации Telegram-бота."""
    token: str  # Токен для доступа к API Telegram
    payments_token: str  # Токен для работы с платежами
    admin_ids: list[int]  # Список ID администраторов бота

@dataclass
class Config:
    """Класс для хранения общей конфигурации приложения."""
    tg_bot: TgBot  # Конфигурация Telegram-бота
    db: Database  # Конфигурация базы данных

# Функция загрузки конфигурации из .env файла
def load_config(path: str | None = None) -> Config:
    """Загружает конфигурацию из .env файла и возвращает объект Config."""
    env = Env()  # Создаем экземпляр класса Env для работы с переменными окружения
    env.read_env(path)  # Читаем переменные окружения из указанного файла .env

    return Config(  # Создаем и возвращаем объект Config
        tg_bot=TgBot(  # Инициализируем объект TgBot
            token=env('BOT_TOKEN'),  # Получаем токен бота из переменных окружения
            payments_token=env('PAYMENTS_TOKEN'),  # Получаем токен для платежей
            admin_ids=list(map(int, env.list('ADMIN_IDS', [])))  # Получаем список ID администраторов, преобразуя их в список целых чисел
        ),
        db=Database(  # Инициализируем объект Database
            host=env('DB_HOST', 'localhost'),  # Получаем хост базы данных, по умолчанию 'localhost'
            port=env.int('DB_PORT', 3306),  # Получаем порт базы данных, по умолчанию 3306
            user=env('DB_USER', 'user'),  # Получаем имя пользователя базы данных, по умолчанию 'user'
            password=env('DB_PASSWORD', 'password'),  # Получаем пароль пользователя, по умолчанию 'password'
            name=env('DB_NAME', 'kyrs')  # Получаем имя базы данных, по умолчанию 'kyrs'
        )
    )
