import time  # Импортируем модуль для работы со временем
import logging  # Импортируем модуль для ведения логов
from datetime import datetime  # Импортируем класс для работы с датами и временем

import requests  # Импортируем библиотеку для выполнения HTTP-запросов
from requests.exceptions import HTTPError, ConnectionError  # Импортируем исключения для обработки ошибок HTTP и соединения


def _get(uri, headers=None, params=None, retries=3, delay=2):
    """Обёртка для выполнения HTTP GET-запроса с повторными попытками."""
    attempt = 0  # Счетчик попыток
    while attempt < retries:  # Пока количество попыток меньше заданного
        try:
            # Выполняем GET-запрос по указанному URI с заголовками и параметрами
            response = requests.get(uri, headers=headers, params=params)
            response.raise_for_status()  # Проверяем статус ответа, выбрасываем исключение при ошибке
            return response  # Возвращаем успешный ответ
        except (HTTPError, ConnectionError) as err:  # Обрабатываем ошибки HTTP и соединения
            logging.error(f"HTTP error occurred: {err}. Retrying {attempt + 1}/{retries}...")  # Логируем ошибку
            attempt += 1  # Увеличиваем счетчик попыток
            if attempt < retries:  # Если есть еще попытки
                time.sleep(delay)  # Пауза перед повторной попыткой
            else:
                logging.error("Max retries reached. Failed to get response.")  # Логируем сообщение о превышении попыток
                raise  # Выбрасываем исключение после максимального количества попыток


class APIFootball:
    """Класс для работы с API Football-Data.org."""
    API_HOST = "https://api.football-data.org/v4"  # Базовый URL API

    def __init__(self, api_key, season):
        """Инициализация класса с API ключом и сезоном."""
        self.API_KEY = api_key  # Сохраняем API ключ
        self.SEASON = season  # Сохраняем сезон

    def _headers(self):
        """Формирование заголовков для запросов."""
        return {
            "X-Auth-Token": self.API_KEY  # Заголовок с API ключом
        }

    def _get_uri(self, path):
        """Создание полного URI для запросов."""
        return f"{self.API_HOST}{path}"  # Формируем полный URI, добавляя путь к базовому URL

    def get_all_leagues(self):
        """Получение списка всех доступных лиг с их ID."""
        uri = self._get_uri("/competitions")  # Формируем URI для получения лиг
        response = _get(uri, headers=self._headers()).json()  # Выполняем GET-запрос и парсим ответ в JSON

        leagues = {}  # Словарь для хранения лиг
        for competition in response['competitions']:  # Проходим по всем соревнованиям
            leagues[competition['name']] = competition['id']  # Сохраняем название лиги и ее ID

        return leagues  # Возвращаем словарь с лигами

    def get_standings(self, league_id):
        """Получение таблицы лиги."""
        uri = self._get_uri(f"/competitions/{league_id}/standings")  # Формируем URI для получения таблицы лиги
        return _get(uri, headers=self._headers())  # Выполняем GET-запрос и возвращаем ответ

    def get_fixtures_leaguedate(self, league_id, date):
        """Получение расписания матчей для указанной лиги на определенную дату."""
        try:
            datetime.strptime(date, "%Y-%m-%d")  # Проверяем формат даты
        except ValueError:
            logging.error("Invalid date format")  # Логируем ошибку неверного формата даты
            raise ValueError("Invalid date format. Correct format is YYYY-MM-DD")  # Выбрасываем исключение

        uri = self._get_uri(f"/competitions/{league_id}/matches")  # Формируем URI для получения матчей
        params = {"date": date}  # Параметры запроса с датой
        return _get(uri, headers=self._headers(), params=params)  # Выполняем GET-запрос и возвращаем ответ

    def get_teams(self, league_id):
        """Получение списка команд для указанной лиги."""
        uri = self._get_uri(f"/competitions/{league_id}/teams")  # Формируем URI для получения команд
        return _get(uri, headers=self._headers())  # Выполняем GET-запрос и возвращаем ответ
