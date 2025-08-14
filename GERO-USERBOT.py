import logging
import asyncio
import random
import aiohttp
import json
import time
import calendar
import re
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors.rpcerrorlist import FloodWaitError, MessageDeleteForbiddenError

# ------------- Конфигурация -------------------
api_id = API_ID  # Ваш api_id
api_hash = 'API_HASH'  # Ваш api_hash
bot_token = None  # Можно оставить None
SESSION_NAME = 'userbot_session'
LOGGING_LEVEL = logging.INFO
PREFIX_FILE = 'prefix_config.json'  # Файл для хранения префикса...
# ----------------------------------------------
logging.basicConfig(level=LOGGING_LEVEL, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)
client = TelegramClient(SESSION_NAME, api_id, api_hash)
WEATHER_API_KEY = 'WEATHER_API'  # Вставьте сюда ваш ключ OpenWeatherMap
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'
start_time = time.time()  # Для uptime

HELP_TEXT = """
Команды GERO-UserBot (префикс команд можно менять с помощью команды setprefix):
{prefix}help - Показать это сообщение
{prefix}echo <текст> - Повторить сообщение
{prefix}rand - Сгенерировать случайное число в диапазоне
{prefix}weather <город> - Погода в городе
{prefix}ascii <текст> - Текст в ASCII art (максимум 20 символов)
{prefix}sticker - Создать стикер из последнего изображения в чате
{prefix}clear - Очистить последние 10 сообщений вашего юзербота
{prefix}setprefix <символ> - Установить префикс для команд (один символ)
{prefix}spam <текст> <кол-во> <интервал в сек> - Отправить спам-сообщения
{prefix}repeatcmd <кол-во> <команда> - Повторить любую команду несколько раз
{prefix}run <команда> - Выполнить любую команду (вывод также подастся как команда)
{prefix}randompic - Отправить случайную картинку
{prefix}time - Показать текущее время сервера
{prefix}uptime - Показать время работы бота
{prefix}ping - Проверить скорость отклика бота
{prefix}flipcoin - Подбросить монетку
{prefix}dice - Бросить кубик (1-6)
{prefix}quote - Поделиться мотивационной цитатой
{prefix}anecdote - Получить случайный анекдот из интернета
{prefix}calendar - Показать календарь текущего месяца
""".strip()

def to_ascii_art(text: str) -> str:
    ascii_map = {
        'A': '/\\', 'B': '|3', 'C': '(', 'D': '|)', 'E': '[-', 'F': '|=',
        'G': '(_+', 'H': '[-]', 'I': '|', 'J': '_|', 'K': '|<', 'L': '|_',
        'M': '|\\/|', 'N': '|\\|', 'O': '()', 'P': '|*', 'Q': '(_,)', 'R': '|2',
        'S': '5', 'T': '+', 'U': '|_|', 'V': '\\/', 'W': '\\/\\/', 'X': '><',
        'Y': '`/', 'Z': '2', ' ': ' '
    }
    return ''.join(ascii_map.get(ch.upper(), ch) for ch in text)

async def fetch_weather(city: str) -> str:
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return f"Ошибка сервера погодного API: Код {resp.status}"
                data = await resp.json()
                if data.get('cod') != 200:
                    return f"Город '{city}' не найден."
                weather = data['weather'][0]['description'].capitalize()
                temp = data['main']['temp']
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                return (f"Погода в {city}:\n"
                        f"{weather}\n"
                        f"Температура: {temp}°C\n"
                        f"Влажность: {humidity}%\n"
                        f"Ветер: {wind} м/с")
    except asyncio.TimeoutError:
        return "Превышено время ожидания ответа от погодного сервиса."
    except Exception as e:
        return f"Ошибка при получении данных о погоде: {e}"

def load_prefix() -> str:
    try:
        with open(PREFIX_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            prefix = data.get('prefix', '/')
            if len(prefix) != 1:
                return '/'
            return prefix
    except Exception:
        return '/'

def save_prefix(prefix: str):
    try:
        with open(PREFIX_FILE, 'w', encoding='utf-8') as f:
            json.dump({'prefix': prefix}, f)
    except Exception as e:
        logger.error(f"Ошибка сохранения префикса: {e}")

def format_uptime(seconds: float) -> str:
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")
    parts.append(f"{sec}с")
    return ' '.join(parts)

QUOTES = [
    "Невозможное возможно, если поверить в себя.",
    "Успех — лестница, на которую нельзя взобраться, держа руки в карманах.",
    "Каждый день - шанс изменить свою жизнь."
]
random.shuffle(QUOTES)

async def fetch_anecdote() -> str:
    url = "https://www.anekdot.ru/random/anekdot/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return "Не удалось получить анекдот, попробуйте позже."
                html = await resp.text()
                # Анекдот содержится в div с классом text
                anecdotes = re.findall(r'<div class="text">([^<]+)</div>', html)
                if anecdotes:
                    return anecdotes[0].strip()
                else:
                    return "Не удалось найти анекдот на странице."
    except Exception as e:
        return f"Ошибка при получении анекдота: {e}"

command_prefix = load_prefix()

async def exec_command(event, cmd, arg_text):
    global command_prefix, QUOTES
    if cmd == 'help':
        await event.respond(HELP_TEXT.format(prefix=command_prefix))
    elif cmd == 'echo':
        if arg_text:
            await event.respond(arg_text)
        else:
            await event.respond("Введите текст для повторения после команды.")
    elif cmd == 'rand':
        try:
            parts = arg_text.split()
            if len(parts) != 2:
                await event.respond(f"Использование: {command_prefix}rand <min> <max>")
                return
            min_num = int(parts[0])
            max_num = int(parts[1])
            if min_num > max_num:
                await event.respond("Ошибка: первый параметр должен быть меньше или равен второму.")
                return
            result = random.randint(min_num, max_num)
            await event.respond(f"Случайное число от {min_num} до {max_num}: {result}")
        except ValueError:
            await event.respond("Параметры должны быть числами.")
    elif cmd == 'weather':
        if not arg_text:
            await event.respond(f"Использование: {command_prefix}weather <город>")
            return
        weather_info = await fetch_weather(arg_text)
        await event.respond(weather_info)
    elif cmd == 'ascii':
        if not arg_text:
            await event.respond(f"Использование: {command_prefix}ascii <текст>")
            return
        if len(arg_text) > 20:
            await event.respond("Слишком длинный текст для ASCII art, максимум 20 символов.")
            return
        ascii_art = to_ascii_art(arg_text)
        await event.respond(f"``````", parse_mode='markdown')
    elif cmd == 'clear':
        me = await client.get_me()
        count = 0
        async for message in client.iter_messages(event.chat_id, from_user=me, limit=30):
            try:
                await message.delete()
                count += 1
                if count >= 10:
                    break
            except MessageDeleteForbiddenError:
                await event.respond("Нет разрешения на удаление сообщений.")
                break
        await event.respond(f"Удалено {count} сообщений.")
    elif cmd == 'sticker':
        reply = await event.get_reply_message()
        if not reply or not reply.photo:
            await event.respond("Пожалуйста, ответьте на сообщение с фотографией.")
            return
        path = await reply.download_media()
        await event.respond(file=path, force_document=False)
        await event.delete()
    elif cmd == 'setprefix':
        new_prefix = arg_text.strip()
        if len(new_prefix) != 1:
            await event.respond("Префикс должен быть одним символом.")
            return
        command_prefix = new_prefix
        save_prefix(command_prefix)
        await event.respond(f"Префикс команд изменён на: {command_prefix}")
    elif cmd == 'menu':
        buttons = [
            [Button.inline('Погода', b'weather')],
            [Button.inline('Рандомное число', b'random')],
            [Button.inline('Помощь', b'help')],
            [Button.inline('Случайная картинка', b'randompic')],
            [Button.inline('Текущее время', b'time')],
            [Button.inline('Время работы (uptime)', b'uptime')],
            [Button.inline('Пинг', b'ping')],
            [Button.inline('Подбросить монетку', b'flipcoin')],
            [Button.inline('Кубик', b'dice')],
            [Button.inline('Цитата', b'quote')],
            [Button.inline('Анекдот', b'anecdote')],
            [Button.inline('Календарь', b'calendar')],
        ]
        await event.respond('Выберите команду:', buttons=buttons)
    elif cmd == 'spam':
        try:
            parts = arg_text.split(' ', 2)
            if len(parts) != 3:
                await event.respond(f"Использование: {command_prefix}spam <текст> <кол-во> <интервал в секундах>")
                return
            spam_text = parts[0]
            count = int(parts[1])
            interval = float(parts[2])
            if count <= 0 or interval < 0:
                await event.respond("Кол-во должно быть > 0, интервал >= 0.")
                return
            if count > 50:
                await event.respond("Максимальное количество сообщений для спама — 50.")
                return
            await event.respond(f"Начинаю спам: {count} сообщений с интервалом {interval} сек.")
            for i in range(count):
                await client.send_message(event.chat_id, spam_text)
                await asyncio.sleep(interval)
            await event.respond("Спам завершён.")
        except ValueError:
            await event.respond(f"Ошибка в параметрах. Использование: {command_prefix}spam <текст> <кол-во> <интервал в секундах>")
    elif cmd == 'repeatcmd':
        try:
            parts = arg_text.split(' ', 1)
            if len(parts) != 2:
                await event.respond(f"Использование: {command_prefix}repeatcmd <кол-во> <команда>")
                return
            count = int(parts[0])
            command_to_repeat = parts[1].strip()
            if count <= 0 or count > 50:
                await event.respond("Количество повторов должно быть от 1 до 50.")
                return
            await event.respond(f"Повторяю команду {count} раз с интервалом 1 секунда.")
            for _ in range(count):
                fake_text = f"{command_prefix}{command_to_repeat}"
                cmd_re, *args_re = fake_text[len(command_prefix):].split(' ', 1)
                arg_text_re = args_re[0] if args_re else ''
                await exec_command(event, cmd_re, arg_text_re)
                await asyncio.sleep(1)
        except ValueError:
            await event.respond(f"Ошибка в параметрах. Использование: {command_prefix}repeatcmd <кол-во> <команда>")
    elif cmd == 'run':
        if not arg_text:
            await event.respond("Введите команду для выполнения с помощью run.")
            return
        old_respond = event.respond
        responses = []

        async def intercept_respond(text, *args, **kwargs):
            responses.append(text)
            return await old_respond(text, *args, **kwargs)

        event.respond = intercept_respond
        try:
            cmd2, *args2 = arg_text.split(' ', 1)
            arg_text2 = args2[0] if args2 else ''
            await exec_command(event, cmd2, arg_text2)
            if responses:
                first_response = responses[0]
                if isinstance(first_response, str) and first_response.startswith(command_prefix):
                    inner_cmd, *inner_args = first_response[len(command_prefix):].split(' ', 1)
                    inner_arg_text = inner_args[0] if inner_args else ''
                    await exec_command(event, inner_cmd, inner_arg_text)
        finally:
            event.respond = old_respond
    elif cmd == 'randompic':
        pics = [
            'https://i.imgur.com/xaRN2Sn.jpg',
            'https://i.imgur.com/v0XAqbM.jpg',
            'https://i.imgur.com/4LxwJmX.jpg',
            'https://i.imgur.com/9RW1PHX.jpg',
            'https://i.imgur.com/gt9whZ5.jpg'
        ]
        url = random.choice(pics)
        await event.respond(file=url)
    elif cmd == 'time':
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await event.respond(f"Текущее время сервера: {now}")
    elif cmd == 'uptime':
        elapsed = time.time() - start_time
        await event.respond(f"Бот работает: {format_uptime(elapsed)}")
    elif cmd == 'ping':
        start = time.perf_counter()
        sent = await event.respond('Пинг...')
        end = time.perf_counter()
        diff = (end - start) * 1000
        await sent.edit(f"Понг! Задержка: {diff:.2f} ms")
    elif cmd == 'flipcoin':
        result = random.choice(['Орёл', 'Решка'])
        await event.respond(f"Подбросил монетку: {result}")
    elif cmd == 'dice':
        result = random.randint(1, 6)
        await event.respond(f"Бросил кубик: {result}")
    elif cmd == 'quote':
        quote = random.choice(QUOTES)
        await event.respond(f"Цитата:\n{quote}")
    elif cmd == 'anecdote':
        anecdote = await fetch_anecdote()
        await event.respond(f"Анекдот:\n{anecdote}")
    elif cmd == 'calendar':
        now = datetime.now()
        cal_text = calendar.month(now.year, now.month)
        await event.respond(f"Календарь на {now.strftime('%B %Y')}\n\n{cal_text}")
    else:
        await event.respond(f"Неизвестная команда: {cmd}. Введите {command_prefix}help для списка команд.")

@client.on(events.NewMessage())
async def command_router(event):
    global command_prefix
    text = event.raw_text
    if not text.startswith(command_prefix):
        return
    cmd, *args = text[len(command_prefix):].split(' ', 1)
    arg_text = args[0] if args else ''
    await exec_command(event, cmd, arg_text)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')
        if data == 'weather':
            await event.answer(f"Введите команду: {command_prefix}weather <город>", alert=True)
        elif data == 'random':
            await event.answer(f"Введите команду: {command_prefix}rand ", alert=True)
        elif data == 'help':
            await event.answer('Показать справку', alert=True)
            await event.edit(HELP_TEXT.format(prefix=command_prefix))
        elif data == 'randompic':
            await event.answer('Отправка случайной картинки', alert=True)
        elif data == 'time':
            await event.answer('Показ времени', alert=True)
        elif data == 'uptime':
            await event.answer('Показ времени работы бота', alert=True)
        elif data == 'ping':
            await event.answer('Проверка задержки', alert=True)
        elif data == 'flipcoin':
            await event.answer('Подбросить монетку', alert=True)
        elif data == 'dice':
            await event.answer('Бросить кубик', alert=True)
        elif data == 'quote':
            await event.answer('Цитата', alert=True)
        elif data == 'anecdote':
            await event.answer('Анекдот', alert=True)
        elif data == 'calendar':
            await event.answer('Показать календарь', alert=True)
        else:
            await event.answer('Неизвестная команда', alert=True)
    except Exception as e:
        logger.error(f"Ошибка в callback: {e}")

@client.on(events.NewMessage(pattern=f'^{command_prefix}logs$'))
async def logs_handler(event):
    await event.respond("Логи выводятся в консоль сервера.")

async def main():
    me = await client.get_me()
    logger.info(f"Userbot запущен от имени: {me.first_name} (@{me.username}) - ID: {me.id}")
    print(f"Userbot работает. Введите {command_prefix}help в Telegram для списка команд.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        try:
            client.loop.run_until_complete(main())
        except FloodWaitError as e:
            logger.warning(f"Превышен лимит запросов. Нужно ждать {e.seconds} секунд.")
        except KeyboardInterrupt:
            logger.info('Userbot остановлен по запросу пользователя.')
        except Exception as e:
            logger.error(f"Необработанное исключение: {e}")
