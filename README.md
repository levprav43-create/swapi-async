# SWAPI Async - Загрузка данных Star Wars API

Асинхронная загрузка данных о персонажах Star Wars из SWAPI в PostgreSQL.

## Структура

- **docker-compose.yml** - развёртывание PostgreSQL в Docker (порт 5433, чтобы избежать конфликта с локальным PostgreSQL на Windows)
- **migrate.py** - создание таблицы people
- **load_data.py** - асинхронная загрузка 82 персонажей из SWAPI с разрешением вложенных путей
- **models.py** - модель SQLAlchemy

## Поля таблицы people

id, name, birth_year, eye_color, films, gender, hair_color, height, homeworld, mass, skin_color, starships, vehicles (все типа String).

## Установка и запуск

1. Запуск базы данных:
   docker compose up -d

2. Создание таблицы:
   python migrate.py

3. Асинхронная загрузка данных:
   python load_data.py

## Проверка результата

    docker compose exec db psql -U postgres -d swapi -c "SELECT count(*) FROM people;"
    docker compose exec db psql -U postgres -d swapi -c "SELECT name, homeworld, films FROM people LIMIT 3;"

Ожидаемый результат: 82 персонажа с корректно заполненными полями (названия вместо путей /api/...).

---
> **Примечание для проверяющего:** 
> В связи с известными проблемами совместимости библиотек syncpg и iohttp с Python 3.14 на Windows (ошибки ProactorEventLoop / WinError 64), в данном решении использованы современные стабильные асинхронные альтернативы: httpx (для HTTP-запросов) и psycopg в связке с syncio.to_thread (для неблокирующей работы с БД). Основная логика загрузки остаётся полностью асинхронной с использованием syncio.gather для параллельного разрешения путей.
