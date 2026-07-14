import asyncio
import sys
import httpx
import psycopg

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_API_URL = "https://swapi-node.vercel.app"
DSN = "postgresql://postgres:postgres@127.0.0.1:5433/swapi"

async def fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Ошибка при запросе {url}: {e}")
        return {}

async def resolve_path(client: httpx.AsyncClient, path: str, key_to_extract: str) -> str:
    if not path:
        return ""
    
    full_url = f"{BASE_API_URL}{path}"
    try:
        data = await fetch_json(client, full_url)
        # ВАЖНО: данные находятся внутри ключа 'fields'
        fields = data.get("fields", {})
        value = fields.get(key_to_extract, "")
        return str(value) if value else ""
    except Exception as e:
        print(f"  ⚠️  Ошибка при разрешении пути {path}: {e}")
        return ""

async def resolve_paths(client: httpx.AsyncClient, paths: list, key_to_extract: str) -> str:
    if not paths:
        return ""
    
    tasks = [resolve_path(client, path, key_to_extract) for path in paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for res in results:
        if isinstance(res, Exception):
            continue
        if res:
            valid_results.append(res)
    
    return ", ".join(valid_results)

async def process_character(client: httpx.AsyncClient, char_data: dict, index: int) -> dict:
    fields = char_data.get("fields", {})
    
    url = fields.get("url", "")
    char_id = url.strip("/").split("/")[-1] if url else str(index + 1)

    homeworld_path = fields.get("homeworld")
    films_paths = fields.get("films", [])
    starships_paths = fields.get("starships", [])
    vehicles_paths = fields.get("vehicles", [])

    # Асинхронно разрешаем пути
    homeworld_task = resolve_path(client, homeworld_path, "name") if homeworld_path else asyncio.sleep(0, result="")
    films_task = resolve_paths(client, films_paths, "title")
    starships_task = resolve_paths(client, starships_paths, "starship_class")
    vehicles_task = resolve_paths(client, vehicles_paths, "name")

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
VALUES (%(id)s, %(name)s, %(birth_year)s, %(eye_color)s, %(films)s, %(gender)s, 
        %(hair_color)s, %(height)s, %(homeworld)s, %(mass)s, %(skin_color)s, 
        %(starships)s, %(vehicles)s)
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
    
    async with httpx.AsyncClient() as client:
        all_characters = []
        page = 1
        
        while True:
            print(f"Загрузка страницы {page}...")
            url = f"{BASE_API_URL}/api/people?page={page}&limit=10"
            data = await fetch_json(client, url)
            
            if not data:
                break
                
            results = data.get("results", [])
            if not results:
                break
                
            tasks = [process_character(client, char, (page-1)*10 + i) for i, char in enumerate(results)]
            processed_chars = await asyncio.gather(*tasks)
            all_characters.extend(processed_chars)
            
            if not data.get("next"):
                break
            page += 1

        print(f"Всего обработано персонажей: {len(all_characters)}")

        print("Сохранение данных в PostgreSQL...")
        
        def save_to_db(characters):
            with psycopg.connect(DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute(DELETE_SQL)
                    for char in characters:
                        cur.execute(INSERT_SQL, char)
                    conn.commit()
        
        await asyncio.to_thread(save_to_db, all_characters)
        print("✅ Данные успешно сохранены в базе данных!")

if __name__ == "__main__":
    asyncio.run(main())