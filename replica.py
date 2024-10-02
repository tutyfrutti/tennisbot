from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import sqlite3
import os
import aiosqlite
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


async def fetch_players():
    # Получаем игроков, отсортированных по рейтингу в порядке убывания
    async with aiosqlite.connect('tennis_club.db') as db:
        async with db.execute('SELECT id, first_name, last_name, rating FROM players ORDER BY rating DESC') as cursor:
            players = await cursor.fetchall()
    return players


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
    cursor.execute('UPDATE tournaments SET image_path = ? WHERE id = ?', (image_path, tournament_id))
    conn.commit()
    conn.close()


async def add_player(first_name, last_name, rating):
    # Добавляем нового игрока в базу данных с автоматическим присвоением ID
    async with aiosqlite.connect('tennis_club.db') as db:
        await db.execute(
            'INSERT INTO players (first_name, last_name, rating) VALUES (?, ?, ?)',
            (first_name, last_name, int(rating))  # Преобразуем рейтинг в int
        )
        await db.commit()


async def get_player(db, first_name: str, surname: str):
    async with db.execute("SELECT * FROM players WHERE first_name = ? AND last_name = ?",
                          (first_name, surname)) as cursor:
        return await cursor.fetchone()


async def delete_player_from_db(first_name: str, last_name: str):
    async with aiosqlite.connect('tennis_club.db') as db:
        player = await get_player(db, first_name, last_name)

        if player:
            await db.execute("DELETE FROM players WHERE first_name = ? AND last_name = ?", (first_name, last_name))
            await db.commit()
            return True  # Успешно удалено
        return False  # Игрок не найден


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

    # Кнопки для администратора
    if callback_query.from_user.id == ADMIN_USER_ID:  # Проверяем, является ли пользователь администратором
        keyboard.append([
            InlineKeyboardButton("Сменить статус", callback_data=f"change_status_{tournament_id}"),
            InlineKeyboardButton("Удалить турнир", callback_data=f"delete_{tournament_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    try:
        # Обновляем сообщение
        await callback_query.message.edit_text(response, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error updating message: {e}")  # Можно добавить логирование


@app.on_callback_query(filters.regex(r"^delete_\d+$"))
async def delete_tournament(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[1])

    # Удаляем турнир из базы данных
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
    conn.commit()
    conn.close()

    await callback_query.message.reply_text("✅ Турнир успешно удалён.")
    await show_tournaments(client, callback_query.message)


@app.on_callback_query(filters.regex(r"^change_status_\d+$"))
async def change_status(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[2])
    tournament = get_tournament_by_id(tournament_id)

    if tournament:
        new_status = 'finished' if tournament[7].strip() == 'active' else 'active'
        conn = sqlite3.connect('tennis_club.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE tournaments SET status = ? WHERE id = ?", (new_status, tournament_id))
        conn.commit()
        conn.close()

        await callback_query.message.reply_text(
            f"Вы уверены, что хотите удалить игрока {first_name} {last_name}?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Удалить", callback_data=f"confirm_delete_{first_name}_{last_name}")],
                [InlineKeyboardButton("Отмена", callback_data="cancel_delete")]
            ])
        )

@app.on_callback_query(filters.regex(r"^delete_player_\d+$"))
async def handle_delete_player(client, callback_query):
    player_index = int(callback_query.data.split("_")[2]) - 1
    players = await fetch_players()

    # Логируем получение игроков
    logging.info(f"Полученные игроки: {players}")

    if player_index < 0 or player_index >= len(players):
        await callback_query.answer("Игрок не найден.")
        return

    player = players[player_index]
    first_name = player[1]
    last_name = player[2]

    # Логируем запрос на удаление игрока
    logging.info(f"Запрос на удаление игрока: {first_name} {last_name}")

    await callback_query.message.reply_text(
        f"Вы уверены, что хотите удалить игрока {first_name} {last_name}?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data=f"confirm_delete_{first_name}_{last_name}")],
            [InlineKeyboardButton("Нет", callback_data="cancel_delete")]
        ])
    )


@app.on_callback_query(filters.regex(r"^confirm_delete_"))
async def confirm_delete_player(client, callback_query):
    data = callback_query.data.split("_")
    first_name = data[2]
    last_name = data[3]

    # Логируем подтверждение удаления игрока
    logging.info(f"Подтверждено удаление игрока: {first_name} {last_name}")

    # Удаляем игрока из базы данных
    deleted = await delete_player_from_db(first_name, last_name)

    if deleted:
        await callback_query.message.reply_text(f"✅ Игрок {first_name} {last_name} успешно удален.")
    else:
        await callback_query.message.reply_text(f"❌ Игрок {first_name} {last_name} не найден.")

    # Обновляем список игроков
    await show_players(client, callback_query.message)

@app.on_callback_query(filters.regex(r"^confirm_delete_"))
async def confirm_delete_player(client, callback_query):
    data = callback_query.data.split("_")
    first_name = data[2]
    last_name = data[3]

    # Логируем подтверждение удаления игрока
    print(f"Подтверждено удаление игрока: {first_name} {last_name}")  # Добавляем лог

    # Удаляем игрока из базы данных
    deleted = await delete_player_from_db(first_name, last_name)

    if deleted:
        await callback_query.message.reply_text(f"✅ Игрок {first_name} {last_name} успешно удален.")
    else:
        await callback_query.message.reply_text(f"❌ Игрок {first_name} {last_name} не найден.")

    # Обновляем список игроков
    await show_players(client, callback_query.message)


@app.on_message(filters.command("register"))
async def register_player(client, message):
    if message.from_user.id == ADMIN_USER_ID:
        await message.reply_text("❗️ Администраторы не могут регистрироваться на турниры.")
        return

    # Логика регистрации игрока


@app.on_message(filters.command("players"))
async def show_players(client, message):
    players = await fetch_players()
    response = "🏅 **Список игроков:**\n\n"
    keyboard = []

    for index, player in enumerate(players, start=1):
        response += f"{index}. {player[1]} {player[2]} - Рейтинг: {player[3]}\n"
        keyboard.append([InlineKeyboardButton("Удалить", callback_data=f"delete_player_{index}")])  # Добавляем кнопку удаления

    await message.reply_text(response, reply_markup=InlineKeyboardMarkup(keyboard))



@app.on_message(filters.command("add_player"))
async def add_player_command(client, message):
    # Логика для добавления игрока
    await message.reply_text("⚠️ Введите имя игрока, фамилию и рейтинг в формате: 'Имя Фамилия Рейтинг'.")


@app.on_message(filters.command("delete_player"))
async def delete_player_command(client, message):
    await message.reply_text("⚠️ Введите имя и фамилию игрока, которого нужно удалить в формате: 'Имя Фамилия'.")

@app.on_message(filters.text)
async def handle_delete_player_response(client, message):
    if message.from_user.id != ADMIN_USER_ID:
        return  # Если не администратор, ничего не делаем

    parts = message.text.split()
    if len(parts) != 2:
        await message.reply_text("⚠️ Пожалуйста, укажите имя и фамилию в правильном формате.")
        return

    first_name, last_name = parts

    # Удаляем игрока из базы данных
    deleted = await delete_player_from_db(first_name, last_name)

    if deleted:
        await message.reply_text(f"✅ Игрок {first_name} {last_name} успешно удален.")
    else:
        await message.reply_text(f"❌ Игрок {first_name} {last_name} не найден.")

@app.on_message(filters.command("admin_menu"))
async def admin_menu(client, message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.reply_text("❗️ У вас нет прав доступа к административному меню.")
        return

    keyboard = [
        [InlineKeyboardButton("Добавить турнир", callback_data="add_tournament")],
        [InlineKeyboardButton("Показать турниры", callback_data="show_tournaments")]
    ]

    await message.reply_text("🔧 **Админ-панель**", reply_markup=InlineKeyboardMarkup(keyboard))


app.run()
