import asyncio
import sys
import psycopg

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

DSN = "postgresql://postgres:postgres@127.0.0.1:5433/swapi"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS people (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    birth_year VARCHAR,
    eye_color VARCHAR,
    films VARCHAR,
    gender VARCHAR,
    hair_color VARCHAR,
    height VARCHAR,
    homeworld VARCHAR,
    mass VARCHAR,
    skin_color VARCHAR,
    starships VARCHAR,
    vehicles VARCHAR
);
"""

async def wait_for_db():
    print("Ожидание готовности базы данных...")
    for i in range(30):
        try:
            with psycopg.connect(DSN) as conn:
                print("✅ База данных готова!")
                return
        except Exception:
            print(f"Попытка {i+1}/30...")
            await asyncio.sleep(2)
    raise Exception("Не удалось подключиться к базе данных")

async def main():
    await wait_for_db()
    print("Подключение к базе данных и создание таблицы...")
    
    def create_table():
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
                conn.commit()
    
    await asyncio.to_thread(create_table)
    print("✅ Таблица 'people' успешно создана!")

if __name__ == "__main__":
    asyncio.run(main())