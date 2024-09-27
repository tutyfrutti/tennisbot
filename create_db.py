import sqlite3


def create_db():
    conn = sqlite3.connect('tennis_club.db')
    cursor = conn.cursor()

    # Создание таблицы турниров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            location TEXT,
            prize_pool TEXT,
            participants_count INTEGER,
            image_path TEXT
        )
    ''')

    # Создание таблицы матчей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            player1 TEXT,
            player2 TEXT,
            score1 INTEGER,
            score2 INTEGER,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
        )
    ''')

    # Создание таблицы игроков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            rating INTEGER
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
