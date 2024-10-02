import aiosqlite
import asyncio

# Функция для очистки таблицы players
async def clear_players_table():
    async with aiosqlite.connect('tennis_club.db') as connection:
        await connection.execute("DELETE FROM players")  # Удаление всех записей
        await connection.commit()  # Сохранение изменений
        print("Таблица players очищена.")

# Основная функция для запуска очистки
async def main():
    await clear_players_table()

# Запуск основной функции
if __name__ == "__main__":
    asyncio.run(main())
