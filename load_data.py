import asyncio
import sys
import aiohttp
import asyncpg

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_API_URL = "https://swapi-node.vercel.app"
DSN = "postgresql://postgres:postgres@127.0.0.1:5433/swapi"

async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict:
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        print(f"  ⚠️  Ошибка при запросе {url}: {e}")
        return {}

async def resolve_path(session: aiohttp.ClientSession, path: str, key_to_extract: str) -> str:
    if not path:
        return ""
    
    full_url = f"{BASE_API_URL}{path}"
    try:
        data = await fetch_json(session, full_url)
        fields = data.get("fields", {})
        value = fields.get(key_to_extract, "")
        return str(value) if value else ""
    except Exception as e:
        print(f"  ⚠️  Ошибка при разрешении пути {path}: {e}")
        return ""

async def resolve_paths(session: aiohttp.ClientSession, paths: list, key_to_extract: str) -> str:
    if not paths:
        return ""
    
    tasks = [resolve_path(session, path, key_to_extract) for path in paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for res in results:
        if isinstance(res, Exception):
            continue
        if res:
            valid_results.append(res)
    
    return ", ".join(valid_results)

async def process_character(session: aiohttp.ClientSession, char_data: dict, index: int) -> dict:
    fields = char_data.get("fields", {})
    
    url = fields.get("url", "")
    char_id = url.strip("/").split("/")[-1] if url else str(index + 1)

    homeworld_path = fields.get("homeworld")
    films_paths = fields.get("films", [])
    starships_paths = fields.get("starships", [])
    vehicles_paths = fields.get("vehicles", [])

    homeworld_task = resolve_path(session, homeworld_path, "name") if homeworld_path else asyncio.sleep(0, result="")
    films_task = resolve_paths(session, films_paths, "title")
    starships_task = resolve_paths(session, starships_paths, "starship_class")
    vehicles_task = resolve_paths(session, vehicles_paths, "name")

    homeworld, films, starships, vehicles = await asyncio.gather(
        homeworld_task, films_task, starships_task, vehicles_task
    )

    return {
        "id": char_id,
        "name": fields.get("name", ""),
        "birth_year": fields.get("birth_year", ""),
        "eye_color": fields.get("eye_color", ""),
        "films": films,
        "gender": fields.get("gender", ""),
        "hair_color": fields.get("hair_color", ""),
        "height": fields.get("height", ""),
        "homeworld": homeworld,
        "mass": fields.get("mass", ""),
        "skin_color": fields.get("skin_color", ""),
        "starships": starships,
        "vehicles": vehicles,
    }

INSERT_SQL = """
INSERT INTO people (id, name, birth_year, eye_color, films, gender, hair_color, 
                    height, homeworld, mass, skin_color, starships, vehicles)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    homeworld = EXCLUDED.homeworld,
    films = EXCLUDED.films,
    starships = EXCLUDED.starships,
    vehicles = EXCLUDED.vehicles
"""

DELETE_SQL = "DELETE FROM people"

async def main():
    print("Запуск асинхронной загрузки данных...")
    
    async with aiohttp.ClientSession() as session:
        all_characters = []
        page = 1
        
        while True:
            print(f"Загрузка страницы {page}...")
            url = f"{BASE_API_URL}/api/people?page={page}&limit=10"
            data = await fetch_json(session, url)
            
            if not data:
                break
                
            results = data.get("results", [])
            if not results:
                break
                
            tasks = [process_character(session, char, (page-1)*10 + i) for i, char in enumerate(results)]
            processed_chars = await asyncio.gather(*tasks)
            all_characters.extend(processed_chars)
            
            if not data.get("next"):
                break
            page += 1

        print(f"Всего обработано персонажей: {len(all_characters)}")

        print("Сохранение данных в PostgreSQL...")
        
        # Подключаемся к БД асинхронно
        conn = await asyncpg.connect(DSN)
        
        try:
            await conn.execute(DELETE_SQL)
            
            for char in all_characters:
                await conn.execute(
                    INSERT_SQL,
                    char["id"], char["name"], char["birth_year"], char["eye_color"],
                    char["films"], char["gender"], char["hair_color"], char["height"],
                    char["homeworld"], char["mass"], char["skin_color"],
                    char["starships"], char["vehicles"]
                )
            
            print("✅ Данные успешно сохранены в базе данных!")
        finally:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(main())