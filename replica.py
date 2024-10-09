from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.types import CallbackQuery
import sqlite3
import os
import aiosqlite
import logging
from pyrogram.types import Message

logging.basicConfig(level=logging. INFO)


# Введи свои данные API
api_id = 23580225  # Заменить на свой API ID
ADMIN_USER_ID = 1499730239
api_hash = "c66fdb54566318ca8f8109e7f8bd52b9"  # Заменить на свой API Hash
bot_token = "7730561175:AAEdZm4YQiUzM87RjcukwrvHuCbQZ2U8_ts"  # Заменить на свой токен бота

# Директория для сохранения изображений
image_dir = "images/"
os.makedirs(image_dir, exist_ok=True)

# Инициализация клиента
app = Client("tennis_club_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


# Словарь для хранения данных о добавлении турнира
tournament_data = {}
# Словарь для хранения данных о добавлении игрока
player_data = {}


async def fetch_player_by_id(player_id):
    async with aiosqlite.connect('tennis_club.db') as db:
        async with db.execute('SELECT first_name, last_name, rating FROM players WHERE id = ?', (player_id,)) as cursor:
            player = await cursor.fetchone()
    return player


async def fetch_players():
    # Получаем игроков, отсортированных по рейтингу в порядке убывания
    async with aiosqlite.connect('tennis_club.db') as db:
        async with db.execute('SELECT id, first_name, last_name, rating FROM players ORDER BY rating DESC') as cursor:
            players = await cursor.fetchall()
    return players


async def delete_all_tournament_images(tournament_id):
    async with aiosqlite.connect('tennis_club.db') as db:
        await db.execute('DELETE FROM tournament_images WHERE tournament_id = ?', (tournament_id,))
        await db.commit()


def get_tournaments():
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tournaments")
    tournaments = cursor.fetchall()
    conn.close()
    return tournaments


def get_tournament_by_id(tournament_id):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
    tournament = cursor.fetchone()
    conn.close()
    return tournament


def save_tournament(name, date, location, prize_pool, participants_count, status='active', image_path=""):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()

    # Получаем максимальный ID из таблицы турниров
    cursor.execute("SELECT MAX(id) FROM tournaments")
    max_id = cursor.fetchone()[0]
    next_id = max_id + 1 if max_id is not None else 1  # Если таблица пуста, начинаем с 1

    cursor.execute('''INSERT INTO tournaments (id, name, date, location, prize_pool, participants_count, image_path, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (next_id, name, date, location, prize_pool, participants_count, image_path, status))
    conn.commit()
    conn.close()


def update_tournament_image(tournament_id, image_path):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tournament_images (tournament_id, image_path)
                      VALUES (?, ?)''', (tournament_id, image_path))
    conn.commit()
    conn.close()

async def fetch_tournament_images(tournament_id):
    async with aiosqlite.connect('tennis_club.db') as db:
        async with db.execute('SELECT image_path FROM tournament_images WHERE tournament_id = ?', (tournament_id,)) as cursor:
            images = await cursor.fetchall()
    return [image[0] for image in images]  # Возвращаем только пути изображений


async def add_player(first_name, last_name, rating):
    async with aiosqlite.connect('tennis_club.db') as db:
        # Получаем максимальный ID из таблицы игроков
        async with db.execute("SELECT MAX(id) FROM players") as cursor:
            max_id = await cursor.fetchone()
            next_id = (max_id[0] + 1) if max_id[0] is not None else 1  # Если таблица пуста, начинаем с 1

        # Добавляем нового игрока в базу данных с автоматическим присвоением ID
        await db.execute(
            'INSERT INTO players (id, first_name, last_name, rating) VALUES (?, ?, ?, ?)',
            (next_id, first_name, last_name,  int(rating))  # Преобразуем рейтинг в int
        )
        await db.commit()


def get_players():
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, rating FROM players ORDER BY rating DESC")
    players = cursor.fetchall()
    conn.close()
    return players



# Функция для записи запроса на регистрацию в турнир
def add_tournament_request(tournament_id, user_id, username, full_name):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tournament_requests (tournament_id, user_id, username, full_name)
        VALUES (?, ?, ?, ?)
    ''', (tournament_id, user_id, username, full_name))
    conn.commit()
    conn.close()


# Функция для получения всех запросов на регистрацию для турнира
def get_tournament_requests(tournament_id):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name FROM tournament_requests WHERE tournament_id = ?", (tournament_id,))
    requests = cursor.fetchall()
    conn.close()
    return requests


@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Добро пожаловать в теннисный бот клуба 'Волна'!\n"
        "Здесь вы можете просмотреть турниры и рейтинги игроков.\n"
        "Используйте команды:\n"
        "/players - посмотреть список игроков и их рейтинги\n"
        "/tournaments - посмотреть доступные турниры"
    )


@app.on_message(filters.command("tournaments"))
async def show_tournaments(client, message):
    tournaments = get_tournaments()
    keyboard = []
    response = "📅 **Список турниров:**\n\n"

    for tournament in tournaments:
        tournament_status = "Активный" if tournament[7].strip() == "active" else "Завершен"
        keyboard.append([InlineKeyboardButton(tournament[1], callback_data=f"show_matches_{tournament[0]}")])
        response += f" {tournament[0]}: {tournament[1]} (Дата: {tournament[2]}, Статус: {tournament_status})\n"

    await message.reply_text(response, reply_markup=InlineKeyboardMarkup(keyboard))


@app.on_message(filters.photo)
async def handle_photo(client, message):
    # Получаем ID турнира из текста сообщения
    tournament_id = None

    if message.caption and message.caption.isdigit():  # Проверяем, является ли текст только цифрами
        tournament_id = int(message.caption)

    if tournament_id is None:
        await message.reply_text("❗️ Пожалуйста, укажите ID турнира в комментарии.")
        return

    # Получаем ID файла фотографии
    photo_file_id = message.photo.file_id  # Получаем ID файла фотографии

    # Сохраняем ID изображения в базе данных
    update_tournament_image(tournament_id, photo_file_id)

    await message.reply_text("✅ Фото успешно добавлено к турниру.")


@app.on_callback_query(filters.regex(r"^show_matches_\d+$"))
async def handle_callback_query(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[2])
    tournament = get_tournament_by_id(tournament_id)

    if not tournament:
        await callback_query.message.reply_text("❗ Турнир не найден.")
        return

    response = f"📅 {tournament[1]} (Дата: {tournament[2]}, Статус: {'Активный' if tournament[7].strip() == 'active' else 'Завершен'})\n\n"
    response += f"📍 Место: {tournament[3]}\n"
    response += f"🏆 Призовой фонд: {tournament[4]}\n"
    response += f"👥 Участников: {tournament[5]}\n\n"
    response += "👥 Зарегистрированные игроки:\n"

    requests = get_tournament_requests(tournament_id)
    if requests:
        for index, req in enumerate(requests, start=1):
            username = req[0]
            full_name = req[1]
            response += f"{index}. {full_name} (@{username})\n"
    else:
        response += "Нет зарегистрированных игроков."

    keyboard = []

    # Проверка статуса турнира для добавления кнопки регистрации
    if tournament[7].strip() == "active":
        keyboard.append([InlineKeyboardButton("Зарегистрироваться", callback_data=f"register_{tournament_id}")])

    # Проверка, является ли пользователь администратором
    if callback_query.from_user.id == ADMIN_USER_ID:
        print(f"Пользователь {callback_query.from_user.id} является администратором.")
        keyboard.append([
            InlineKeyboardButton("Сменить статус", callback_data=f"change_status_{tournament_id}"),
            InlineKeyboardButton("Удалить турнир", callback_data=f"delete_{tournament_id}"),
            InlineKeyboardButton("Удалить фото", callback_data=f"delete_all_photos_{tournament_id}")  # Новая кнопка
        ])
    else:
        print(f"Пользователь {callback_query.from_user.id} не администратор. Кнопки администратора не будут добавлены.")

    # Если кнопок нет, устанавливаем reply_markup в None
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    try:
        # Обновляем сообщение
        await callback_query.message.edit_text(response, reply_markup=reply_markup)

        # Получаем и отправляем все изображения турнира
        images = await fetch_tournament_images(tournament_id)
        for image_path in images:
            await callback_query.message.reply_photo(photo=image_path)

    except Exception as e:
        await callback_query.message.reply_text("❗ Произошла ошибка при обновлении сообщения.")

    await callback_query.answer()


@app.on_callback_query(filters.regex(r"^delete_all_photos_\d+$"))
async def handle_delete_all_photos(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[3])  # Получаем ID турнира

    await delete_all_tournament_images(tournament_id)  # Удаляем все изображения

    await callback_query.message.reply_text("✅ Все фотографии турнира успешно удалены.")
    await callback_query.answer()


# Словарь для временного хранения состояний пользователей
user_states = {}


@app.on_callback_query(filters.regex(r"^register_\d+$"))
async def register_for_tournament(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username

    # Проверка, не зарегистрирован ли пользователь ранее
    requests = get_tournament_requests(tournament_id)
    if any(req[0] == username for req in requests):
        await callback_query.answer("Вы уже зарегистрировались на этот турнир.", show_alert=True)
        return

    # Запрашиваем имя и фамилию у пользователя
    user_states[user_id] = {"tournament_id": tournament_id, "username": username}
    await callback_query.message.reply_text("Пожалуйста, введите ваше имя и фамилию:",
                                            reply_markup=ForceReply(selective=True))
    await callback_query.answer()


@app.on_message(filters.text & filters.reply)
async def handle_name_surname(client, message):
    user_id = message.from_user.id
    full_name = message.text.strip()

    # Проверяем, есть ли состояние для пользователя
    if user_id in user_states:
        tournament_id = user_states[user_id]["tournament_id"]
        username = user_states[user_id]["username"]

        # Добавляем запрос на регистрацию в базу данных
        add_tournament_request(tournament_id, user_id, username, full_name)

        await message.reply_text("Вы успешно зарегистрировались на турнир!")

        # Очищаем состояние пользователя
        del user_states[user_id]
    else:
        await message.reply_text("Произошла ошибка. Попробуйте еще раз.")



@app.on_callback_query(filters.regex(r"^delete_\d+$") & filters.user(ADMIN_USER_ID))
async def delete_tournament_callback(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[1])
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
    conn.commit()
    cursor.execute("DELETE FROM tournament_requests WHERE tournament_id = ?", (tournament_id,))
    conn.commit()
    conn.close()

    await callback_query.answer("Турнир успешно удален.", show_alert=True)
    await callback_query.message.delete()


@app.on_callback_query(filters.regex(r"^change_status_\d+$") & filters.user(ADMIN_USER_ID))
async def change_status_callback(client, callback_query):
    try:
        # Извлекаем ID турнира из callback_data
        tournament_id = int(
            callback_query.data.split("_")[2])  # Исправлено на 2, если используется 'change_status_{id}'

        # Получаем информацию о турнире
        tournament = get_tournament_by_id(tournament_id)

        if tournament is None:
            await callback_query.answer("Турнир не найден.", show_alert=True)
            return

        # Определяем новый статус турнира
        new_status = "finished" if tournament[7].strip() == "active" else "active"

        # Обновляем статус в базе данных
        conn = sqlite3.connect('tennis_club.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE tournaments SET status = ? WHERE id = ?', (new_status, tournament_id))
        conn.commit()
        conn.close()

        await callback_query.answer(
            f"Статус турнира изменен на {'Завершен' if new_status == 'finished' else 'Активный'}.", show_alert=True)
        await callback_query.message.delete()

    except (IndexError, ValueError):
        await callback_query.answer("Произошла ошибка при изменении статуса турнира.", show_alert=True)
    except Exception as e:
        await callback_query.answer("Произошла ошибка. Попробуйте снова.", show_alert=True)
        print(f"Ошибка: {e}")  # Логируем ошибку для отладки


@app.on_message(filters.command("players"))
async def display_players(client, message):
    players = await fetch_players()

    # Формируем сообщение с рейтингом игроков
    response = "👥 Рейтинг игроков:\n"
    for index, player in enumerate(players, start=1):
        response += f"{index} - {player[1]} {player[2]} - Рейтинг: {player[3]}\n"

    # Создаем кнопки для админа
    admin_buttons = [
        [InlineKeyboardButton("Удалить участника", callback_data="delete_player")],
        [InlineKeyboardButton("Изменить рейтинг", callback_data="change_rating")]
    ]
    reply_markup = InlineKeyboardMarkup(admin_buttons)

    # Отправляем сообщение с результатом и кнопками
    await message.reply_text(response, reply_markup=reply_markup)


@app.on_message(filters.command("admin_menu") & filters.user(ADMIN_USER_ID))
async def admin_menu(client, message):
    keyboard = [
        [InlineKeyboardButton("Добавить турнир", callback_data='add_tournament')],
        [InlineKeyboardButton("Добавить игрока", callback_data='add_player')]  # Добавляем кнопку для добавления игрока
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text('Админ-меню:', reply_markup=reply_markup)


@app.on_callback_query(filters.regex(r"^add_player$") & filters.user(ADMIN_USER_ID))
async def add_player_callback(client, callback_query):
    await callback_query.message.reply_text("🔍 Введите имя игрока:")
    player_data[callback_query.from_user.id] = {'step': 'first_name'}
    await callback_query.answer()  # Отвечаем на callback query


@app.on_callback_query(filters.regex(r"^add_tournament$") & filters.user(ADMIN_USER_ID))
async def add_tournament_callback(client, callback_query):
    # Запрашиваем название турнира
    await callback_query.message.reply_text("🔍 Введите название турнира:")
    tournament_data[callback_query.from_user.id] = {'step': 'name'}
    await callback_query.answer()  # Отвечаем на callback query


@app.on_message(filters.command("add_tournament"))
async def add_tournament_command(client, message):
    await message.reply_text("🔍 Введите название турнира:")
    tournament_data[message.from_user.id] = {'step': 'name'}

@app.on_message(filters.command("add_player"))
async def add_player_command(client, message):
    await message.reply_text("🔍 Введите имя игрока:")
    player_data[message.from_user.id] = {'step': 'first_name'}

@app.on_message(filters.text & filters.user(ADMIN_USER_ID))
async def handle_input(client, message):
    user_id = message.from_user.id

    # Обработка добавления турнира
    if user_id in tournament_data:
        step = tournament_data[user_id]['step']

        if step == 'name':
            tournament_data[user_id]['name'] = message.text
            tournament_data[user_id]['step'] = 'date'
            await message.reply_text("🔍 Введите дату турнира (YYYY-MM-DD):")

        elif step == 'date':
            tournament_data[user_id]['date'] = message.text
            tournament_data[user_id]['step'] = 'location'
            await message.reply_text("🔍 Введите место турнира:")

        elif step == 'location':
            tournament_data[user_id]['location'] = message.text
            tournament_data[user_id]['step'] = 'prize_pool'
            await message.reply_text("🔍 Введите призовой фонд:")

        elif step == 'prize_pool':
            tournament_data[user_id]['prize_pool'] = message.text
            tournament_data[user_id]['step'] = 'participants_count'
            await message.reply_text("🔍 Введите количество участников:")

        elif step == 'participants_count':
            tournament_data[user_id]['participants_count'] = message.text

            # Сохранение турнира в базе данных
            save_tournament(
                tournament_data[user_id]['name'],
                tournament_data[user_id]['date'],
                tournament_data[user_id]['location'],
                tournament_data[user_id]['prize_pool'],
                tournament_data[user_id]['participants_count']
            )
            await message.reply_text("✅ Турнир успешно добавлен!")
            del tournament_data[user_id]

    # Обработка добавления игрока
    elif user_id in player_data:
        step = player_data[user_id]['step']

        if step == 'first_name':
            player_data[user_id]['first_name'] = message.text
            player_data[user_id]['step'] = 'last_name'
            await message.reply_text("🔍 Введите фамилию игрока:")

        elif step == 'last_name':
            player_data[user_id]['last_name'] = message.text
            player_data[user_id]['step'] = 'rating'
            await message.reply_text("🔍 Введите рейтинг игрока:")

        elif step == 'rating':
            player_data[user_id]['rating'] = message.text

            # Сохранение игрока в базе данных
            await add_player(  # Добавлено await
                player_data[user_id]['first_name'],
                player_data[user_id]['last_name'],
                player_data[user_id]['rating']
            )
            await message.reply_text("✅ Игрок успешно добавлен!")
            del player_data[user_id]



@app.on_callback_query(filters.regex("delete_player") & filters.user(ADMIN_USER_ID))
async def delete_player(client, callback_query):
    players = await fetch_players()
    keyboard = []

    for player in players:
        keyboard.append([InlineKeyboardButton(f"{player[1]} {player[2]} - Рейтинг: {player[3]}", callback_data=f"confirm_delete_{player[0]}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.message.reply_text("Выберите игрока для удаления:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^confirm_delete_\d+$") & filters.user(ADMIN_USER_ID))
async def confirm_delete_player(client, callback_query):
    player_id = int(callback_query.data.split("_")[2])

    async with aiosqlite.connect('tennis_club.db') as db:
        await db.execute("DELETE FROM players WHERE id = ?", (player_id,))
        await db.commit()

    await callback_query.answer("Игрок успешно удален.", show_alert=True)
    await callback_query.message.delete()


@app.on_message(filters.text & filters.user(ADMIN_USER_ID))
async def handle_input(client, message):
    user_id = message.from_user.id

    # Обработка изменения рейтинга
    if user_id in player_data:
        step = player_data[user_id]['step']

        if step == 'player_id':
            player_id = message.text
            player_data[user_id]['player_id'] = player_id
            player_data[user_id]['step'] = 'new_rating'
            await message.reply_text("🔍 Введите новый рейтинг игрока:")

        elif step == 'new_rating':
            new_rating = message.text
            player_id = player_data[user_id]['player_id']

            # Проверяем, существует ли игрок
            if await player_exists(player_id):
                await change_player_rating(player_id, new_rating)
                await message.reply_text("✅ Рейтинг игрока успешно изменен!")
            else:
                await message.reply_text("❌ Игрок с указанным ID не найден.")
            del player_data[user_id]

            # Смена рейтинга в базе данных
            await change_player_rating(player_id, new_rating)

            await message.reply_text("✅ Рейтинг игрока успешно изменен!")
            del player_data[user_id]


rating_change_data = {}

@app.on_callback_query(filters.regex("change_rating") & filters.user(ADMIN_USER_ID))
async def change_rating_callback(client, callback_query):
    players = await fetch_players()  # Предполагаем, что эта функция возвращает список игроков

    # Формируем сообщение с рейтингом игроков
    response = "🔍 Выберите игрока для изменения рейтинга:\n"
    keyboard = []

    for index, player in enumerate(players, start=1):
        keyboard.append(
            [InlineKeyboardButton(f"{index}. {player[1]} {player[2]}", callback_data=f"select_player_{player[0]}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.message.reply_text(response, reply_markup=reply_markup)
    await callback_query.answer()


# Обработчик выбора игрока по нажатию на кнопку
@app.on_callback_query(filters.regex(r"^select_player_(\d+)$") & filters.user(ADMIN_USER_ID))
async def select_player_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    player_id = int(callback_query.data.split('_')[-1])



if __name__ == "__main__":
    app.run()
