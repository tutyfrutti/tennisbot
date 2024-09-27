from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import os

# Введи свои данные API
api_id = 23580225  # Заменить на свой API ID
api_hash = "c66fdb54566318ca8f8109e7f8bd52b9"  # Заменить на свой API Hash
bot_token = "7730561175:AAEdZm4YQiUzM87RjcukwrvHuCbQZ2U8_ts"  # Заменить на свой токен бота

# Директория для сохранения изображений
image_dir = "images/"
os.makedirs(image_dir, exist_ok=True)

# Инициализация клиента
app = Client("tennis_club_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

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

def save_tournament(name, date, location, prize_pool, participants_count, image_path=""):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tournaments (name, date, location, prize_pool, participants_count, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, date, location, prize_pool, participants_count, image_path))
    conn.commit()
    conn.close()

def update_tournament_image(tournament_id, image_path):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tournaments
        SET image_path = ?
        WHERE id = ?
    ''', (image_path, tournament_id))
    conn.commit()
    conn.close()

def add_player(first_name, last_name, rating):
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO players (first_name, last_name, rating)
        VALUES (?, ?, ?)
    ''', (first_name, last_name, rating))
    conn.commit()
    conn.close()

def get_players():
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, rating FROM players ORDER BY rating DESC")
    players = cursor.fetchall()
    conn.close()
    return players

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
    for tournament in tournaments:
        keyboard.append([InlineKeyboardButton(tournament[1], callback_data=f"show_matches_{tournament[0]}")])

    await message.reply_text(
        "📅 **Список турниров:**\n\n" + "\n".join(
            [f"- {tournament[1]} (Дата: {tournament[2]})" for tournament in tournaments]),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex(r"^show_matches_\d+$"))
async def handle_callback_query(client, callback_query):
    tournament_id = int(callback_query.data.split("_")[2])
    tournament = get_tournament_by_id(tournament_id)

    if not tournament:
        await callback_query.message.reply_text("❗ Турнир не найден.")
        return

    response = f"📅 {tournament[1]} (Дата: {tournament[2]})\n\n"
    response += f"📍 Место: {tournament[3]}\n"
    response += f"🏆 Призовой фонд: {tournament[4]}\n"
    response += f"👥 Участников: {tournament[5]}\n\n"
    response += "📊 Результаты матчей:\n"

    if callback_query.message.text != response:
        await callback_query.message.edit_text(response)
    else:
        print("Текст сообщения не изменился, редактирование не требуется.")

    if tournament[6]:
        await callback_query.message.reply_photo(photo=tournament[6])

    await callback_query.answer()

@app.on_message(filters.command("players"))
async def show_players(client, message):
    players = get_players()
    if players:
        response = "🎾 Список игроков и их рейтинги:\n\n"
        response += "\n".join([f"- {first_name} {last_name} (Рейтинг: {rating})" for first_name, last_name, rating in players])
    else:
        response = "❗ Игроки не найдены."

    await message.reply_text(response)


@app.on_message(filters.command("add_tournament") & filters.user([1499730239]))  # Замените на свой user_id админа
async def add_tournament(client, message):
    try:
        # Убираем команду и пробелы
        command, rest = message.text.split(maxsplit=1)

        # Ожидается формат: Название,Дата,Место,Призовой_фонд,Количество_участников
        parts = rest.split(",", 4)

        if len(parts) != 5:
            raise ValueError("Некорректное количество аргументов. Ожидается 5 параметров, разделенных запятыми.")

        # Извлекаем параметры
        name = parts[0].strip()
        date = parts[1].strip()
        location = parts[2].strip()
        prize_pool = parts[3].strip()
        participants_count = int(parts[4].strip())

        # Подключаемся к базе данных
        conn = sqlite3.connect('tennis_club.db')
        cursor = conn.cursor()

        # Находим максимальный ID текущих турниров
        cursor.execute("SELECT MAX(id) FROM tournaments")
        max_id = cursor.fetchone()[0]
        if max_id is None:
            new_id = 1
        else:
            new_id = max_id + 1

        # Сохраняем новый турнир с новым ID
        cursor.execute('''
            INSERT INTO tournaments (id, name, date, location, prize_pool, participants_count, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (new_id, name, date, location, prize_pool, participants_count, ""))
        conn.commit()
        conn.close()

        await message.reply_text(
            f"✅ Турнир '{name}' добавлен с ID {new_id} на дату {date} в месте {location} с призовым фондом {prize_pool} и {participants_count} участниками. Теперь загрузите изображение для этого турнира.")
    except ValueError as ve:
        await message.reply_text(
            f"❗ Ошибка: {str(ve)}. Пожалуйста, используйте правильный формат: /add_tournament Название,Дата,Место,Призовой_фонд,Количество_участников")
    except Exception as e:
        await message.reply_text(f"⚠️ Ошибка: {str(e)}")


@app.on_message(filters.command("delete_tournament") & filters.user([1499730239]))  # Замените на свой user_id админа
async def delete_tournament(client, message):
    try:
        # Ожидается формат: /delete_tournament Название
        parts = message.text.split(maxsplit=1)

        if len(parts) != 2:
            raise ValueError("Неправильный формат. Ожидается формат: /delete_tournament Название")

        # Убираем команду
        command, tournament_name = parts

        # Проверяем, существует ли турнир с таким названием
        conn = sqlite3.connect('tennis_club.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tournaments WHERE name = ?", (tournament_name.strip(),))
        tournament = cursor.fetchone()

        if not tournament:
            raise ValueError(f"Турнир с названием '{tournament_name.strip()}' не найден.")

        tournament_id = tournament[0]

        # Удаляем турнир
        cursor.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
        conn.commit()
        conn.close()

        await message.reply_text(f"✅ Турнир с названием '{tournament_name.strip()}' успешно удален.")
    except ValueError as ve:
        await message.reply_text(f"❗ Ошибка: {str(ve)}")
    except Exception as e:
        await message.reply_text(f"⚠️ Ошибка: {str(e)}")


@app.on_message(filters.photo & filters.user([1499730239]))  # Замените на свой user_id админа
async def handle_photo(client, message):
    if message.caption:
        try:
            tournament_id = int(message.caption.strip())  # Номер турнира
            update_tournament_image(tournament_id, message.photo.file_id)
            await message.reply_text(f"✅ Изображение добавлено к турниру #{tournament_id}.")
        except ValueError:
            await message.reply_text("❗ Пожалуйста, укажите правильный номер турнира в тексте.")
    else:
        await message.reply_text("❗ Пожалуйста, укажите номер турнира в тексте.")

@app.on_message(filters.command("add_player") & filters.user([1499730239]))  # Замените на свой user_id админа
async def add_player_command(client, message):
    try:
        # Ожидается формат: /add_player Имя Фамилия Рейтинг
        _, first_name, last_name, rating = message.text.split(" ", 3)
        add_player(first_name, last_name, int(rating))
        await message.reply_text(f"✅ Игрок {first_name} {last_name} с рейтингом {rating} добавлен.")
    except ValueError:
        await message.reply_text(
            "❗ Пожалуйста, используйте правильный формат: /add_player Имя Фамилия Рейтинг")
    except Exception as e:
        await message.reply_text(f"⚠️ Ошибка: {str(e)}")

if __name__ == "__main__":
    app.run()
