from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
import logging
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)

API_TOKEN = ("your_bot_api_token") # Можно получить в @BotFather

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Регулярное выражение для проверки валидности URL
url_regex = re.compile(
    r'^(https?:\/\/)?'  # опциональный http:// или https://
    r'(([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}|@[a-zA-Z0-9\-]+)$',  # доменное имя или @username
    re.IGNORECASE)  # опциональный путь

async def get_bot_username():
    bot_info = await bot.get_me()
    return bot_info.username

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    bot_username = await get_bot_username()
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Вставить юзернейм бота", switch_inline_query_current_chat=f"@{bot_username}")
    )
    await message.reply(f"Привет!\nЯ бот для создания инлайн кнопок!\n"
                        f"Используйте формат @{bot_username} {{текст сообщения}} {{сыллка}} {{текст кнопки}} "
                        f"для создания инлайн кнопок.", reply_markup=markup)

# Обработчик для инлайн команд
async def inline_handler(query: types.InlineQuery):
    try:
        parts = query.query.split(' ', 2)
        if len(parts) < 3:
            bot_username = await get_bot_username()
            result = types.InlineQueryResultArticle(
                id='1',
                title='Инструкция',
                input_message_content=types.InputTextMessageContent(
                    f'Пожалуйста, используйте формат: @{bot_username} {{текст сообщения}} {{ссылка}} {{текст кнопки}}'
                ),
            )
            await query.answer([result], cache_time=1, is_personal=True)
        else:
            message_text = parts[0]
            button_text = parts[-1]
            button_url = ' '.join(parts[1:-1])  # Объединяем все части между первой и последней вводимой частью

            if not message_text or not button_text or not button_url:
                raise ValueError("Все части команды должны быть заполнены.")

            if not re.match(url_regex, button_url) and '.' not in button_url:
                raise ValueError("URL недействителен. Пожалуйста, введите действительный URL.")

            # Если URL начинается с @, обрабатываем его как валидный URL
            if button_url.startswith('@'):
                button_url = 'https://t.me/' + button_url[1:]

            # Если URL не содержит протокол, добавим http:// по умолчанию
            if not button_url.startswith(('http://', 'https://')) and not button_url.startswith('https://t.me/'):
                button_url = 'https://' + button_url

            # Определяем, где находится ссылка и формируем кнопку
            if '.' in button_url or button_url.startswith('@'):
                message_text = f'{message_text} {button_url}'
            else:
                button_text = f'{button_url} {button_text}'

            buttons = InlineKeyboardMarkup().add(
                InlineKeyboardButton(button_text, url=button_url)
            )
            
            result = types.InlineQueryResultArticle(
                id='2',
                title='Создать кнопку',
                input_message_content=types.InputTextMessageContent(message_text),
                reply_markup=buttons
            )

            await query.answer([result], cache_time=1, is_personal=True)
    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        result = types.InlineQueryResultArticle(
            id='3',
            title='Ошибка',
            input_message_content=types.InputTextMessageContent(f'Ошибка: {ve}')
        )
        await query.answer([result], cache_time=1, is_personal=True)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        result = types.InlineQueryResultArticle(
            id='4',
            title='Ошибка',
            input_message_content=types.InputTextMessageContent('Произошла неожиданная ошибка. Пожалуйста, попробуйте снова позже.')
        )
        await query.answer([result], cache_time=1, is_personal=True)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)