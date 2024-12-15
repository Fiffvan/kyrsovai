from aiogram.types import CallbackQuery  # Импортируем класс CallbackQuery для обработки нажатий на кнопки
from aiogram_dialog import Dialog, DialogManager, StartMode, Window  # Импортируем классы для работы с диалогами
from aiogram_dialog.widgets.kbd import Button, Row  # Импортируем классы для создания кнопок и строк
from aiogram_dialog.widgets.text import Const  # Импортируем класс для создания текстовых констант
from aiogram.dispatcher.router import Router  # Импортируем класс Router для маршрутизации
from aiogram.fsm.state import State, StatesGroup  # Импортируем классы для работы с состояниями
from handlers.table import send_league_standings  # Импортируем функцию для отправки таблицы лиги

# Определяем состояния для диалога
class LeagueSG(StatesGroup):
    select_league = State()  # Состояние выбора лиги

# Обработчики нажатий на кнопки
async def premier_league_clicked(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик для нажатия кнопки Премьер-лиги."""
    await send_league_standings(callback.message, "Premier League")  # Отправляем таблицу Премьер-лиги

async def la_liga_clicked(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик для нажатия кнопки Ла Лиги."""
    await send_league_standings(callback.message, "Primera Division")  # Отправляем таблицу Ла Лиги

async def bundesliga_clicked(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик для нажатия кнопки Бундеслиги."""
    await send_league_standings(callback.message, "Bundesliga")  # Отправляем таблицу Бундеслиги

async def serie_a_clicked(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик для нажатия кнопки Серии А."""
    await send_league_standings(callback.message, "Serie A")  # Отправляем таблицу Серии А

async def ligue_1_clicked(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик для нажатия кнопки Лиги 1."""
    await send_league_standings(callback.message, "Ligue 1")  # Отправляем таблицу Лиги 1

async def help_clicked(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик для нажатия кнопки Помощь."""
    # Отправляем сообщение с описанием лиг
    await callback.message.answer("Помощь: Выберите лигу, чтобы посмотреть её таблицу. Премьер-лига: это певый английский футбольный дивизион🇬🇧"
                                  "Ла Лига: это певый испанский футбольный дивизион 🇪🇸"
                                  "Бундеслига: это певый немецкий футбольный дивизион 🇩🇪"
                                  "Серия А: это певый итальянский футбольный дивизион 🇮🇹 \n"
                                  "Лига 1: это певый французкий футбольный дивизион 🇫🇷")

# Определяем кнопки и окно диалога
select_league_window = Window(
    Const("Выберите чемпионат:"),  # Заголовок окна
    Row(  # Первая строка с кнопками
        Button(Const("Премьер-лига"), id="premier_league", on_click=premier_league_clicked),  # Кнопка для Премьер-лиги
        Button(Const("Ла Лига"), id="la_liga", on_click=la_liga_clicked),  # Кнопка для Ла Лиги
    ),
    Row(  # Вторая строка с кнопками
        Button(Const("Бундеслига"), id="bundesliga", on_click=bundesliga_clicked),  # Кнопка для Бундеслиги
        Button(Const("Серия А"), id="serie_a", on_click=serie_a_clicked),  # Кнопка для Серии А
    ),
    Row(  # Третья строка с кнопками
        Button(Const("Лига 1"), id="ligue_1", on_click=ligue_1_clicked),  # Кнопка для Лиги 1
        Button(Const("Помощь"), id="help", on_click=help_clicked),  # Кнопка для помощи
    ),
    state=LeagueSG.select_league,  # Устанавливаем состояние для окна
)

# Создаем диалог
leagues_dialog = Dialog(select_league_window)  # Создаем диалог с окном выбора лиги

# Создаем маршрутизатор
leagues_router = Router()  # Создаем экземпляр маршрутизатора
leagues_router.include_router(leagues_dialog)  # Включаем диалог в маршрутизатор
