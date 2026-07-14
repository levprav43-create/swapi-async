import asyncio
import sys
import httpx
import psycopg

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_API_URL = "https://swapi-node.vercel.app"
DSN = "postgresql://postgres:postgres@127.0.0.1:5433/swapi"

async def fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url)
    response.raise_for_status()
    return response.json()

async def resolve_path(client: httpx.AsyncClient, path: str, key_to_extract: str) -> str:
    if not path:
        return ""
    
    full_url = f"{BASE_API_URL}{path}"
    try:
        data = await fetch_json(client, full_url)
        return str(data.get(key_to_extract, ""))
    except Exception:
        return ""

async def resolve_paths(client: httpx.AsyncClient, paths: list, key_to_extract: str) -> str:
    if not paths:
        return ""
    
    tasks = [resolve_path(client, path, key_to_extract) for path in paths]
    results = await asyncio.gather(*tasks)
    
    valid_results = [res for res in results if res]
    return ", ".join(valid_results)

async def process_character(client: httpx.AsyncClient, char_data: dict) -> dict:
    fields = char_data.get("fields", {})
    
    url = fields.get("url", "")
    char_id = url.strip("/").split("/")[-1] if url else ""

    homeworld_task = resolve_path(client, fields.get("homeworld"), "name")
    films_task = resolve_paths(client, fields.get("films", []), "title")
    starships_task = resolve_paths(client, fields.get("starships", []), "starship_class")
    vehicles_task = resolve_paths(client, fields.get("vehicles", []), "name")

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
            
            results = data.get("results", [])
            if not results:
                break
                
            tasks = [process_character(client, char) for char in results]
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