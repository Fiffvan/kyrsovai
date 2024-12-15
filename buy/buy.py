import logging  # Импортируем модуль для ведения логов
from aiogram import Bot, types  # Импортируем класс Bot и типы из библиотеки aiogram
from aiogram import Router  # Импортируем класс Router для маршрутизации
from aiogram.filters import Command  # Импортируем фильтр для команд
from config_data.config import load_config  # Импортируем функцию для загрузки конфигурации
from database.database import get_db_connection  # Импортируем функцию для получения соединения с базой данных

# Загружаем конфигурацию из файла
config = load_config()

# Настраиваем уровень логирования
logging.basicConfig(level=logging.INFO)

# Инициализируем бота с токеном из конфигурации
bot = Bot(token=config.tg_bot.token)
router = Router()  # Создаем экземпляр маршрутизатора

# Определяем цену подписки на 1 месяц (500 рублей, указано в копейках)
PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=500 * 100)  # в копейках (руб)

# Обработка команды 'buy'
@router.message(Command('buy'))  # Используем фильтр Command для команды 'buy'
async def buy(message: types.Message):
    # Проверяем, является ли токен платежей тестовым
    if config.tg_bot.payments_token.split(':')[1] == 'TEST':
        await bot.send_message(message.chat.id, "Тестовый платеж!!!")  # Отправляем сообщение о тестовом платеже

    # Отправляем пользователю счет на оплату
    await bot.send_invoice(message.chat.id,
                           title="Подписка на бота",  # Заголовок счета
                           description="Активация подписки на бота на 1 месяц",  # Описание счета
                           provider_token=config.tg_bot.payments_token,  # Токен провайдера платежей
                           currency="rub",  # Валюта
                           photo_url="https://www.aroged.com/wp-content/uploads/2024/11/On-Xbox-Series-X-You-can-already-play-the-750x536.jpg",  # URL изображения
                           photo_width=416,  # Ширина изображения
                           photo_height=234,  # Высота изображения
                           photo_size=416,  # Размер изображения
                           is_flexible=False,  # Указываем, что цена фиксированная
                           prices=[PRICE],  # Список цен
                           start_parameter="one-month-subscription",  # Параметр для начала платежа
                           payload="test-invoice-payload")  # Полезная нагрузка для предоплаты (должна быть обработана в течение 10 секунд)

# Обработка предварительного запроса на оплату
@router.pre_checkout_query(lambda query: True)  # Фильтр, который позволяет пропускать все предварительные запросы
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)  # Подтверждаем предварительный запрос на оплату

# Обработка успешного платежа
@router.message(lambda message: message.successful_payment)  # Фильтр для успешных платежей
async def successful_payment(message: types.Message):
    logging.info("Платеж получен. Обработка...")  # Логируем получение платежа

    payment_info = message.successful_payment  # Получаем информацию о платеже
    for k, v in payment_info.dict().items():  # Перебираем информацию о платеже и логируем ее
        logging.info(f"{k} = {v}")

    user_id = message.from_user.id  # Получаем ID пользователя

    conn = await get_db_connection()  # Получаем соединение с базой данных
    if conn is None:  # Если соединение не удалось получить
        await message.answer("Ошибка при подключении к базе данных. Попробуйте позже.")  # Отправляем сообщение об ошибке
        return

    try:
        # Обновляем статус подписки в базе данных
        async with conn.cursor() as cursor:  # Открываем курсор для выполнения запроса
            await cursor.execute(
                "UPDATE users SET subscription_active = 1, subscription_date = NOW(), subscription_paid = 1 WHERE user_id = %s",
                (user_id,)  # Обновляем данные для текущего пользователя
            )
            await conn.commit()  # Подтверждаем изменения в базе данных

        logging.info(f"Подписка пользователя с ID {user_id} успешно активирована.")  # Логируем успешную активацию подписки

        # Отправляем пользователю сообщение об успешной активации подписки
        await message.answer(
            f"Платеж на сумму {payment_info.total_amount // 100} {payment_info.currency} прошел успешно! Ваша подписка активирована."
        )
    except Exception as e:  # Обрабатываем возможные исключения
        logging.error(f"Ошибка при обновлении статуса подписки: {e}")  # Логируем ошибку
        await message.answer("Ошибка при обновлении статуса подписки. Попробуйте позже.")  # Отправляем сообщение об ошибке
    finally:
        conn.close()  # Закрываем соединение с базой данных
