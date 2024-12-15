# handlers/table.py

import logging  # Для ведения логов
import os  # Для работы с переменными окружения
import re  # Для работы с регулярными выражениями
from aiogram import Dispatcher, types  # Импорт классов для работы с Aiogram
from datetime import datetime  # Для работы с датами и временем
from utils.api import APIFootball  # Импорт класса для работы с API футбольной статистики
import pytz  # Для работы с временными зонами

# Получение API ключа и сезона из переменных окружения
api_key = os.getenv("API_KEY")
SEASON = os.getenv("SEASON")
apif = APIFootball(api_key=api_key, season=SEASON)  # Создание экземпляра API с ключом и сезоном

def format_standings(standings):
    """Функция для форматирования таблицы standings в строку для отправки пользователю."""
    max_team_name_length = 30  # Максимальная длина названия команды
    msg_text = "__*Таблица лиги:*__\n"  # Заголовок таблицы
    msg_text += '```\n'  # Начало блока кода для форматирования
    msg_text += f'{"Команда":<{max_team_name_length}} М   В   Н   П   РГ   ЗГ   ПГ   О\n'  # Заголовок таблицы
    msg_text += '-' * (max_team_name_length + 40) + '\n'  # Разделитель между заголовком и данными

    # Проходим по каждой команде в standings и добавляем ее данные в msg_text
    for team in standings:
        team_name = team['team']['name']  # Получаем название команды
        if len(team_name) > max_team_name_length:
            team_name = team_name[:max_team_name_length - 3] + '...'  # Обрезаем название, если оно слишком длинное

        # Получаем статистику команды
        played = team['playedGames']
        won = team['won']
        draw = team['draw']
        lost = team['lost']
        goals_for = team['goalsFor']
        goals_against = team['goalsAgainst']
        goal_difference = goals_for - goals_against
        points = team['points']

        # Форматируем строку с данными команды и добавляем ее в msg_text
        msg_text += f'{team_name:<{max_team_name_length}} {played:<3} {won:<3} {draw:<3} {lost:<3} {goals_for:<4} {goals_against:<4} {goal_difference:<4} {points:<4}\n'

    msg_text += '```'  # Закрытие блока кода
    return msg_text  # Возвращаем отформатированное сообщение

async def send_league_standings(message: types.Message, league_name: str):
    """Отправляет таблицу лиги, эмблему и флаг."""
    try:
        leagues = apif.get_all_leagues()  # Получаем все лиги
        league_id = leagues.get(league_name)  # Получаем ID для указанной лиги

        if league_id is None:
            await message.answer("Не удалось найти ID лиги. Проверьте правильность имени.")
            return  # Если ID лиги не найден, отправляем сообщение и выходим из функции

        response = apif.get_standings(league_id).json()  # Получаем данные о таблице лиги

        if 'competition' in response:  # Проверяем, есть ли данные о соревновании
            competition = response['competition']
            area = competition.get('area', {})  # Получаем информацию о стране
            emblem_url = competition.get('emblem')  # Получаем URL эмблемы лиги
            flag_url = area.get('flag')  # Получаем URL флага страны

            # Если есть эмблема, отправляем ее пользователю
            if emblem_url:
                await message.answer_photo(emblem_url, caption=f"Эмблема лиги: {competition['name']}")
            # Если есть флаг, отправляем его пользователю
            if flag_url:
                await message.answer_photo(flag_url, caption=f"Флаг страны: {area['name']}")

        # Если есть данные о standings, форматируем их и отправляем
        if 'standings' in response and response['standings']:
            standings = response['standings'][0]['table']  # Получаем таблицу
            msg_text = format_standings(standings)  # Форматируем таблицу
            await message.answer(msg_text, parse_mode="MarkdownV2")  # Отправляем таблицу
        else:
            await message.answer("Таблица лиги недоступна.")  # Если таблица недоступна, отправляем сообщение

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")  # Обрабатываем ошибки и отправляем сообщение

async def show_today_matches(message: types.Message):
    """Отправляет информацию о матчах, запланированных на сегодня."""
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")  # Получаем сегодняшнюю дату в формате YYYY-MM-DD
        leagues = {  # Словарь с лигами и их ID
            "Premier League": 2021,
            "La Liga": 2014,
            "Bundesliga": 2002,
            "Serie A": 2019,
            "Ligue 1": 2015
        }

        msg_text = "Matches today:\n"  # Начинаем сообщение о матчах

        # Проходим по всем лигам и получаем информацию о матчах на сегодня
        for league_name, league_id in leagues.items():
            response = apif.get_fixtures_leaguedate(league_id, today_date).json()  # Получаем данные о матчах
            logging.info(f"API response for {league_name}: {response}")  # Логируем ответ API

            if 'matches' in response and response['matches']:  # Проверяем, есть ли матчи
                msg_text += f"\n{league_name}:\n"  # Добавляем название лиги в сообщение
                for match in response['matches']:
                    match_time = match['utcDate']  # Получаем время матча в UTC
                    match_date = match_time.split('T')[0]  # Извлекаем только дату

                    if match_date == today_date:  # Проверяем, совпадает ли дата матча с сегодняшней
                        home_team = match['homeTeam']['name']  # Название домашней команды
                        away_team = match['awayTeam']['name']  # Название выездной команды

                        # Преобразуем время из UTC в Московское время
                        try:
                            match_time_utc = datetime.strptime(match_time, "%Y-%m-%dT%H:%M:%SZ")  # Преобразуем строку в объект datetime
                            match_time_utc = match_time_utc.replace(tzinfo=pytz.utc)  # Устанавливаем временную зону UTC
                            moscow_tz = pytz.timezone("Europe/Moscow")  # Устанавливаем временную зону для Москвы
                            match_time_msk = match_time_utc.astimezone(moscow_tz)  # Преобразуем время в Московское
                            match_time_msk_str = match_time_msk.strftime("%d-%m %H:%M")  # Форматируем время для вывода
                        except ValueError:
                            match_time_msk_str = "Неизвестное время"  # Если произошла ошибка, устанавливаем значение по умолчанию

                        # Добавляем информацию о матче в сообщение
                        msg_text += f"{home_team} vs {away_team} at {match_time_msk_str} MSK\n"
            else:
                msg_text += f"\n{league_name}: No matches today.\n"  # Если матчей нет, указываем это в сообщении

        # Экранирование символов, которые могут вызвать проблемы в Markdown
        msg_text = re.sub(r'([._\-!|])', r'\\\1', msg_text)

        # Проверяем, превышает ли длина текста максимальный лимит Telegram
        max_length = 4096
        while len(msg_text) > max_length:
            # Отправляем часть текста и обрезаем его на следующую итерацию
            part_text = msg_text[:max_length]
            await message.answer(part_text, parse_mode="MarkdownV2")
            msg_text = msg_text[max_length:]

        # Отправляем остаток текста, если он есть
        if msg_text:
            await message.answer(msg_text, parse_mode="MarkdownV2")
    except Exception as e:
        logging.error(f"Ошибка при получении матчей: {e}")  # Логируем ошибку
        await message.answer(f"Ошибка: {str(e)}")  # Отправляем сообщение об ошибке

# Функции для обработки команд, связанных с таблицами лиг
async def cmd_apl(message: types.Message):
    await send_league_standings(message, "Premier League")  # Отправляем таблицу Премьер-лиги

async def cmd_laliga(message: types.Message):
    await send_league_standings(message, "Primera Division")  # Отправляем таблицу Ла Лиги

async def cmd_bundesliga(message: types.Message):
    await send_league_standings(message, "Bundesliga")  # Отправляем таблицу Бундеслиги

async def cmd_serie_a(message: types.Message):
    await send_league_standings(message, "Serie A")  # Отправляем таблицу Серии А

async def cmd_ligue_1(message: types.Message):
    await send_league_standings(message, "Ligue 1")  # Отправляем таблицу Лиги 1

# Регистрация всех обработчиков команд
def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_apl, lambda message: message.text == "Премьер-лига")  # Обработчик для Премьер-лиги
    dp.message.register(cmd_laliga, lambda message: message.text == "Ла Лига")  # Обработчик для Ла Лиги
    dp.message.register(cmd_bundesliga, lambda message: message.text == "Бундеслига")  # Обработчик для Бундеслиги
    dp.message.register(cmd_serie_a, lambda message: message.text == "Серия А")  # Обработчик для Серии А
    dp.message.register(cmd_ligue_1, lambda message: message.text == "Лига 1")  # Обработчик для Лиги 1
    dp.message.register(show_today_matches, lambda message: message.text == "Матчи на сегодня")  # Обработчик для матчей на сегодня

def register_today_matches_handler(dp: Dispatcher):
    dp.message.register(show_today_matches, lambda message: message.text == "Матчи на сегодня")  # Регистрация обработчика для матчей на сегодня
