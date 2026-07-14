# SWAPI Async - Загрузка данных Star Wars API

Асинхронная загрузка данных о персонажах Star Wars из SWAPI в PostgreSQL.

## Структура

- **docker-compose.yml** - развёртывание PostgreSQL в Docker
- **migrate.py** - создание таблицы people
- **load_data.py** - асинхронная загрузка 82 персонажей из SWAPI
- **models.py** - модель SQLAlchemy

## Поля таблицы people

- id, name, birth_year, eye_color, films, gender, hair_color
- height, homeworld, mass, skin_color, starships, vehicles

## Установка и запуск

    docker compose up -d
    python migrate.py
    python load_data.py

## Проверка результата

    docker compose exec db psql -U postgres -d swapi -c "SELECT count(*) FROM people;"

Ожидаемый результат: 82 персонажа.

