# Prompt Log
## Задание Повышенной сложности 1: Создание полноценного веб-приложения
### Промпт 1
**Инструмент:** Auto режим в Cursor.
**Промпт:** "You need to help me create a Taxi order service web app. simplest interface. First task is - Bootstrap a FastAPI project with SQLAlchemy + SQLite. Create models for: `User` (id, name, email, hashed_password, role), `Order` (id, client_id, driver_id, tariff_id, status, created_at, pickup, destination), `Driver` (id, user_id, car, is_available), `Tariff` (id, name, price_per_km), `Payment` (id, order_id, amount, status, paid_at). Include Alembic migrations, a project folder structure, and a `/health` endpoint. Work in a current directory, create a logical file structure"
**Результат:** Базовая структура файловая струтура приложения, базы данных, автогенерирующейся документации (swagger). Работающий сервер, запустил uvicorn.
### Промпт 2
**Инструмент:** Auto режим в Cursor.
**Промпт:**
**Результат:** 
### Итого
- Количество промптов: 
- Что пришлось исправлять вручную:
- Время: ~
---
